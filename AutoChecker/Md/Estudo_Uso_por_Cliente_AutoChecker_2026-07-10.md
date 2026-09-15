# Estudo de Uso por Cliente — AutoChecker

**Fonte:** Grafana Loki (produção) · **Janela:** últimos 7 dias (~03/07 a 10/07/2026) · **Gerado:** 10/07/2026

> Objetivo: identificar, **por cliente**, o tempo/intensidade de uso, as páginas e funções mais utilizadas, os documentos compartilhados e o mapeamento de tenants do AutoChecker.

---

## 0. Resumo executivo

- **A "Base Compartilhada" é, sozinha, ~85% do uso web** do produto — mas é um **tenant multi-empresa**: dentro dela operam várias distribuidoras de combustível (Copercana, Rede Petro, Small, Biopetro, Setta, Larco, Flexpetro e outras), identificáveis só pelo **domínio do e-mail** do usuário.
- **Dois retratos diferentes de "cliente"** que não batem: quem **navega no app web** (api.log) ≠ quem **mais processa documentos** (worker). Clientes de alto processamento (Logum, Unibras, Atvos, Watt, Vopak, PetroRio) **quase não aparecem no log web** — usam integração/mobile/API. Isso é um **ponto cego de observabilidade de uso**.
- **~75% do tráfego web é *polling* de fundo** (badge de notificações, permissões, status de trial), não uso de funcionalidade. As ações reais concentram-se em **listar / visualizar / enviar documentos** e **gestão de usuários**.
- **Duas perguntas não têm resposta nos logs de hoje**: **tipo de documento** (não é logado) e **tempo de sessão real** (não há evento de sessão). Ambas exigem instrumentação — ver §7.
- Achado colateral de segurança: bots varrendo `/.env` em produção (§6).

---

## 1. Metodologia e limitações

**De onde vêm os dados (Grafana Loki, `env=prod`):**

| Job | Arquivo | Conteúdo | Uso neste estudo |
|-----|---------|----------|------------------|
| `autochecker-backend` | `/var/log/autochecker/api.log` | Requisições HTTP (método, rota, status, duração, **tenant**, usuário, IP) | Páginas, funções e uso web por cliente |
| `celery-tasks` | `/var/log/celery/tasks.log` | Tarefas de processamento (OCR, extração, classificação, autenticação) | Documentos processados por cliente |

**Limitações (sem inventar o que não está no log):**
- ⚠️ **Tempo de sessão não é medido** — não há evento login→logout. "Tempo de uso" aqui é **aproximado por**: nº de requisições, tempo de processamento no servidor (soma de `duration_ms`), usuários ativos distintos e dias ativos. **Não** é tempo de tela do usuário.
- ⚠️ **Tipo de documento não é logado** — o worker registra apenas `schema` do tenant + UUID do documento; o upload é multipart (`request_body: null`). Logo, "tipos de documento por cliente" **não sai do Loki hoje**.
- O label `tenant` do Loki é sempre `public` (schema do Postgres); o **cliente real** está *dentro* da linha (`tenant.schema` / `tenant.name`, ou o 1º argumento das tarefas do worker).
- Janela de 7 dias — números são de uma semana, não histórico.

---

## 2. Mapa de tenants → clientes

Cada cliente é um **schema de tenant** no Postgres. Observados na janela:

### 2.1 Clientes de negócio (produção)

| Tenant (schema) | Cliente | Observação |
|---|---|---|
| `base_compartilhada` | **Base Compartilhada** | ⚠️ **Multi-empresa** — várias distribuidoras compartilham o schema (ver §2.2) |
| `tecab_2cf34e0a` | **Tecab** | Perfil de administração/config |
| `logum_logistica_s_a` | **Logum Logística S.A.** | Alto processamento, sem uso web |
| `unibraspe` | **Unibras PE** | Alto processamento, sem uso web |
| `atvos` / `atvos_bioenergia` | **Atvos (Bioenergia)** | Dois schemas |
| `watt_distribuidora_brasileira_de_combust_7661c69e` | **Watt Distribuidora** | |
| `vopak_4327c3a2` | **Vopak** | |
| `petrorio_dbc9b891` | **PetroRio** | Majoritariamente reprocessamento |
| `petroserra_f7c70c21` | **Petroserra** | |
| `idaza` | **Idaza** | |
| `ciapetro` | **Ciapetro** | |
| `guterres_comercio_de_combustiveis` | **Guterres Comércio de Combustíveis** | Uso leve |
| `ultracargo_logistica` | **Ultracargo Logística** | Uso leve |

### 2.2 Sub-clientes dentro da "Base Compartilhada"

Como o schema é compartilhado, os clientes finais só se distinguem pelo **domínio do e-mail** (nº de requisições web, 7d):

| Empresa | Domínio | Req. web (7d) |
|---|---|---:|
| **Copercana** | copercana.com.br | 5.862 |
| **Rede Petro** | redepetro.com.br | 5.382 |
| **Small** | small.com.br | 2.248 |
| **Biopetro** | biopetro.com.br | 1.617 |
| **Setta Combustíveis** | settacombustiveis.com.br | 973 |
| **Larco Petróleo** | larcopetroleo.com.br | 835 |
| **Flexpetro** | flexpetro.com | 773 |
| **Petronac** | petronac.com.br | 184 |
| **Midas Combustíveis** | midascombustiveis.com | 184 |
| **GP Combustíveis** | gpcombustiveis.com.br | 146 |
| _(equipe AutoChecker operando na base)_ | autochecker.cloud | 3.059 |
| _(contas administrativas da base)_ | basecompartilhada.com.br | 3.333 |

### 2.3 Não-clientes (excluir das análises de negócio)

- **Canal**: `mobile` (é o app mobile, não um cliente).
- **Demo/comercial**: `demonstracao_comercial` ("Demonstração Comercial").
- **Internos/teste Automind**: `automind`, `automind_2_dc8b63db`, `automind_v2`, `automind_qa`, `automind_teste_fcc16395`; `public` ("Portal de Gestão de Assinantes", admin da plataforma); `luisg`, `tarcisiosa_4deb6781` (contas de dev).

> **Achado**: a nomenclatura de schema é **inconsistente** — uns limpos (`unibraspe`, `atvos`, `idaza`), outros com sufixo UUID (`tecab_2cf34e0a`, `vopak_4327c3a2`). Padronizar facilitaria toda análise por cliente.

---

## 3. Intensidade / "tempo de uso" por cliente

**Uso do app web** (api.log, 7d) — requisições, tempo de processamento no servidor e usuários ativos distintos:

| Cliente | Requisições | Tempo servidor (Σ duration) | Usuários ativos |
|---|---:|---:|---:|
| **Base Compartilhada** (todas as empresas) | 24.821 | ~34,3 min | 23 |
| **Tecab** | 2.547 | ~1,9 min | 2 |
| **Guterres** | 175 | ~15 s | 1 |
| **Demonstração Comercial** (demo) | 52 | ~2 s | 1 |
| **Ultracargo** | 14 | ~1 s | 1 |
| _Automind V2 (interno)_ | 2.190 | ~2,2 min | 5 |
| _Portal Assinantes (public, interno)_ | 465 | ~1,7 min | 1 |
| _Mobile (canal)_ | 183 | ~24 s | 3 |

**Distribuição diária (Base Compartilhada, req/dia):** 1.730 → 2.049 → 1.067 → 598 → **7.859 (pico)** → 5.314 → 5.221 → **121 (fim de semana)** → 3.435. Uso claramente **dias úteis**, com queda quase total no fim de semana. **Tecab** só começa a aparecer a partir de ~06/07 (cliente em rampa).

> ⚠️ Estes números **não** são "horas de uso" — são proxies de intensidade. Tempo de sessão real exige instrumentação (§7).

---

## 4. Páginas mais utilizadas

### 4.1 Geral (7d) — apenas rotas de **ação do usuário**

Somente o que uma pessoa **decidiu fazer** no sistema. As rotas de *polling* de fundo foram removidas desta tabela — não representam uso, e sim o app se atualizando sozinho.

| Rota | O que significa (leitura executiva) | Chamadas |
|---|---|---:|
| **`/api/documents/?...ordering=-created_at`** | **Listar documentos.** Abrir a tela principal e ver os documentos recebidos, com ordenação e filtros. É a "caixa de entrada" do produto — o gesto mais repetido do dia a dia. | **641** |
| `/api/accounts/users/all_users/` | **Consultar usuários da empresa.** Ver quem tem acesso ao sistema. Uso administrativo, não operacional — típico de quem gerencia a conta, não de quem processa documentos. | 263 |
| **`/api/documents/<id>/view/`** | **Abrir um documento.** Carregar o arquivo em si (imagem/PDF) para conferência visual. É quando a pessoa efetivamente *lê* o documento, não apenas o vê na lista. | ~200 |
| `/api/documents/<id>/tags/` | **Etiquetar um documento.** Marcar com tags para organizar e reencontrar depois. Indica cliente que já estruturou um processo próprio em cima do produto. | ~170 |
| **`POST /api/documents/upload/multi/`** | **Enviar documentos para validação.** A ação que gera valor: dispara o pipeline OCR → extração → classificação → autenticação. Cada chamada vira custo de processamento e entrega de resultado. | 113 |
| `/api/validation/site-monitoring/` | **Conferir disponibilidade das fontes externas.** Status dos sites/órgãos de onde o AutoChecker extrai dados na validação. Quem olha isso costuma estar investigando por que um documento não validou. | 82 |

As ações acima somam **~1.469 chamadas** na semana, contra ~30 mil requisições totais. Não é o universo completo de ações (rotas de menor volume ficaram fora do top), mas dá a ordem de grandeza: **uso deliberado é uma fração pequena do tráfego**.

> **Insight-chave**: retirando o ruído, o uso real se resume a dois blocos — **documentos** (listar → abrir → etiquetar → enviar) e **administração** (usuários). E dentro do bloco de documentos, **listar pesa 5,7× mais que enviar**: os clientes usam muito mais o produto para *consultar* o que já chegou do que para *alimentar* a esteira pela web.

**3 rotas ficaram de fora por não serem classificáveis como ação pura**: `all-tenants-switcher` (1.402), `notifications/inbox/?page_size=50` (1.250) e `legal/acceptances/status/` (739) são disparadas *junto com* o carregamento de tela — o usuário até pode ter clicado, mas o volume não distingue clique de carga automática. Contá-las como ação inflaria o número de uso real.

<details>
<summary>Tabela original completa (com polling), para referência</summary>

| Rota | Chamadas | Natureza |
|---|---:|---|
| `/api/notifications/inbox/unread_count/` | 15.654 | 🔄 Polling (badge de notificações) |
| `/api/core/permissions/` | 5.924 | 🔄 Polling (permissões) |
| `/api/trial/status/` | 1.767 | 🔄 Polling (status trial) |
| `/api/tenants/all-tenants-switcher/` | 1.402 | Carregamento / troca de tenant |
| `/api/notifications/inbox/?page_size=50` | 1.250 | Abrir central de notificações |
| `/api/documents/upload-usage/` | 1.056 | 🔄 Polling (cota de upload) |
| `/api/legal/acceptances/status/` | 739 | Termos / LGPD |
| **`/api/documents/?...ordering=-created_at`** | **641** | ✅ **Listar documentos** |
| `/api/accounts/me/` | 633 | Perfil |
| `/api/accounts/users/all_users/` | 263 | Gestão de usuários |
| `/api/accounts/groups/all-groups/` | 223 | Gestão de grupos |
| **`/api/documents/<id>/view/`** | ~200 | ✅ **Visualizar documento** |
| **`POST /api/documents/upload/multi/`** | 113 | ✅ **Enviar documentos** |
| `/api/documents/<id>/tags/` | ~170 | ✅ Tags de documento |
| `/api/documents/processed/` | 82 | Documentos processados |
| `/api/validation/site-monitoring/` | 82 | ✅ Monitoramento de sites |

Nesta visão completa, **~75% do tráfego é polling de fundo** (unread_count + permissions + trial/status + upload-usage) — é o que justifica a tabela enxuta acima.

</details>

### 4.2 Por cliente (rotas reais, excluindo polling)

**Base Compartilhada** — perfil "operação de documentos":
- Notificações (central) 985 · **Listar documentos 731** · Tenants-switcher 975 · Legal/termos 476 · **Visualizar documento 252** · **Tags 168** · **Upload 96** · Integrações (logs 44 / providers 32) · Entidades (veículo 33 / motorista 19) · Site-monitoring 34 · Reprocessar 35.

**Tecab** — perfil "administração/configuração":
- **Gestão de usuários forte**: all_users 118 · all-groups 107 · update/unsuspend usuário 16+16 · atribuir grupo 16. Notificações 119 · **Visualizar documento 48** · Listar documentos 43 · Tenants-switcher 120 · trial 148. Pouco upload web.

**Guterres** — perfil "consulta leve":
- Notificações 19 · Listar documentos 8 · Processados 16 · Site-monitoring 16 · Tenants-switcher 19.

---

## 5. Funções mais utilizadas por cliente

Agrupando rotas em áreas funcionais + o pipeline de processamento do worker.

### 5.1 Áreas funcionais do app (quem usa o quê)
- **Documentos** (listar, visualizar, enviar, tags, reprocessar): **Base Compartilhada** domina; Tecab usa visualização; Guterres consulta.
- **Gestão de usuários/grupos**: **Tecab** é o mais intenso (proporcionalmente), seguido de Base Compartilhada.
- **Integrações** (logs/providers): praticamente só **Base Compartilhada**.
- **Entidades** (motorista/veículo): só **Base Compartilhada**.
- **Monitoramento de sites**: Base, Tecab e Guterres.

### 5.2 Pipeline de processamento de documentos (worker) — documentos processados por cliente

Contagem de `classify_document` (≈ 1 por documento), 7d:

| Cliente | Documentos processados |
|---|---:|
| **Base Compartilhada** | 3.365 |
| Demonstração Comercial (demo) | 300 |
| **Unibras PE** | 252 |
| **Logum Logística** | 198 |
| _Mobile (canal)_ | 130 |
| **Idaza** | 78 |
| **Watt Distribuidora** | 51 |
| **Atvos** | 27 |
| **Vopak** | 21 |
| **Tecab** | 14 |
| **Ultracargo** | 12 |
| **Guterres** | 5 |
| **PetroRio / Petroserra** | 3 cada |

> Cada documento percorre **OCR → extração → classificação → autenticação**. A autenticação (`authenticate_document`) roda várias vezes por documento (ex. Base: 7.766 autenticações para 3.365 documentos) — bom sinal de que a etapa de autenticação é a mais custosa e a que mais falha/reprocessa.

---

## 6. Tipos de documentos compartilhados por cliente

### ⚠️ Lacuna de dados
O **tipo/categoria do documento não é registrado em lugar nenhum do Loki**:
- O worker loga apenas `schema` do tenant + **UUID** do documento (sem tipo).
- O upload (`POST /api/documents/upload/multi/`) é multipart e o `request_body` sai como `null` no log.

**Não é possível, hoje, quebrar documentos por tipo via Grafana.** (Sinalizado em vez de inventar.) O AutoChecker valida documentos fiscais/regulatórios de distribuidoras (certidões, licenças etc.), mas o tipo específico está só no banco, não no log.

### Proxy disponível — volume de documentos "compartilhados" (enviados) por cliente
"Compartilhar documento" no AutoChecker = **enviar para validação** (não há endpoint de "share"; a única ação de compartilhamento externo é o *link de acesso externo*, sem tráfego relevante na janela).

- **Uploads web** (`POST upload/multi`, 7d): Base Compartilhada **96** · Tecab **6** · Guterres **3**.
- **Documentos processados** (proxy mais completo, inclui integração/mobile): ver tabela §5.2.

Para responder de fato "tipos por cliente", é preciso instrumentar `document_type` (§7).

---

## 7. Achados adicionais e recomendações

### Achados
1. **Ponto cego de uso**: os clientes que mais processam documentos (Logum, Unibras, Atvos, Watt, Vopak, PetroRio) **não aparecem no log web** — operam por integração/mobile/API, que não registram requisição com o tenant no `api.log`. A visão "uso web" subestima esses clientes.
2. **Segurança**: bots varrendo `/api/.env/`, `/api/shared/.env/`, `/api/shared/config/.env/` (IPs como 93.123.109.x) à procura de segredos. Retornam 404, mas é ruído/ataque contínuo.
3. **PII/LGPD**: o `api.log` grava `user_email` e `ip` em texto claro (já mapeado na auditoria de 10/07). Este estudo foi feito **sem expor e-mails/IPs individuais**, só identidades de empresa.
4. **Polling excessivo**: `unread_count` sozinho = 15,6 mil chamadas/semana. Custo de infra e ruído de log evitáveis.

### Recomendações de instrumentação (para fechar as lacunas)
1. **Logar `document_type`/`category`** no `classify_document` e no upload → habilita "tipos de documento por cliente".
2. **Logar `tenant_name` e `user_id` (hash)** como campos estruturados, e **emitir evento de sessão** (login/heartbeat/logout) → habilita "tempo de uso real" e dashboards por cliente sem parsing frágil.
3. **Instrumentar os canais mobile/integração** com o tenant real → elimina o ponto cego (§7.1).
4. **Reduzir polling** (unread_count/permissions/trial) via WebSocket/SSE ou backoff.
5. **Bloquear varredura de `.env`** no WAF/edge.
6. **Padronizar a nomenclatura de schema** de tenant (sem sufixo UUID quando possível).

---

_Dados extraídos ao vivo do Grafana Loki (datasource "loki") em 10/07/2026. Consultas LogQL disponíveis mediante solicitação. Base Compartilhada é multi-empresa; números por sub-cliente são aproximados pelo domínio de e-mail._
