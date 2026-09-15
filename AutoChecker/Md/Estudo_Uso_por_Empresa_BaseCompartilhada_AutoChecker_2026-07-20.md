# Estudo de Uso por Empresa — AutoChecker (Base Compartilhada)

**Janela:** 20/06/2026 a 20/07/2026 (30 dias) · **Ambiente:** produção · **Tenant:** `base_compartilhada`
**Fonte:** Grafana/Loki — dashboard *AutoChecker — Uso por Cliente*, job `autochecker-backend` (`api.log`)
**Gerado em:** 20/07/2026

> ⚠️ **Confidencial — contém PII.** O estudo agrega por domínio de e-mail e cita e-mails de usuários finais. Uso interno. Ver [Auditoria LGPD de logs](Auditoria_LGPD_Logs_Grafana_Loki_AutoChecker_2026-07-10.md).

---

## 1. Resumo executivo

Em 30 dias, **12 empresas clientes** (24 usuários) usaram o AutoChecker pela Base Compartilhada, somando **97.682 requisições** e **~905 horas** de aplicação aberta.

Três leituras que mudam decisão:

1. **A Base Compartilhada é, na prática, a Copercana.** Sozinha ela responde por **~60% do tráfego** e **~56% do tempo de uso** de todos os clientes. As outras 11 empresas somam menos que ela.
2. **89,5% de tudo que trafega é polling**, não uso deliberado. De 122.248 requisições, só **12.860 (10,5%)** são ações de fato — o resto é o app "respirando" (`unread_count`, `permissions`, `trial/status`). Isso é custo de infraestrutura sem valor de negócio.
3. **O produto está sendo usado como consulta, não como esteira de processamento.** Foram apenas **385 uploads** em 30 dias entre todos os clientes. A função campeã quase universal é *listar/buscar documentos* — as pessoas entram para **olhar** documentos que chegaram por outra via (integração/API), não para enviá-los.

---

## 2. Ranking de empresas — 30 dias

Ordenado por **tempo de uso** (proxy de janelas de 30 min ativas — ver §5).

| # | Empresa | Tempo de uso | Dias ativos | Usuários | Requisições | Uploads | Função mais usada¹ | Erro |
|---|---------|-------------:|------------:|---------:|------------:|--------:|--------------------|-----:|
| 1 | **Copercana** | **503,0 h** | 29 | 6 | 58.462 | 135 | Listar/buscar documentos | 0,70% |
| 2 | **Rede Petro** | 119,0 h | 19 | 4 | 15.280 | 68 | Listar/buscar documentos | 0,04% |
| 3 | **Flexpetro** | 84,5 h | 20 | 1 | 5.803 | 62 | Listar/buscar documentos | 0,09% |
| 4 | **Setta Combustíveis** | 45,5 h | 6 | 1 | 3.713 | 22 | Consultar processados | 0,00% |
| 5 | **Larco Petróleo** | 40,5 h | 13 | 2 | 4.091 | 16 | Listar/buscar documentos | **5,89%** |
| 6 | **Biopetro** | 39,0 h | 15 | 2 | 4.387 | 24 | Visualizar documento | 0,82% |
| 7 | **Small** | 38,0 h | 9 | 1 | 3.058 | 19 | Listar/buscar documentos | 0,29% |
| 8 | **GP Combustíveis** | 14,5 h | 11 | 2 | 1.188 | 23 | Upload de documentos | 0,25% |
| 9 | **Midas Combustíveis** | 10,5 h | 3 | 2 | 1.096 | 3 | Consultar processados | 0,00% |
| 10 | **Petronac** | 4,5 h | 5 | 1 | 256 | 10 | Upload de documentos | 0,00% |
| 11 | **Argemil Distribuidora** | 3,5 h | 2 | 1 | 242 | 3 | Listar/buscar documentos | 0,00% |
| 12 | **BP** | 2,5 h | 2 | 1 | 106 | 0 | Config. de notificações | 0,00% |
| | **Total clientes** | **905,0 h** | — | **24** | **97.682** | **385** | — | 0,72% |

¹ Excluindo notificações e rotas de polling — ver §5 sobre por que "Ler notificações" foi descartado do topo.

### Contas não-cliente (excluídas do ranking)

| Conta | Tempo | Requisições | O que é |
|-------|------:|------------:|---------|
| `basecompartilhada.com.br` (6 usuários) | 143,0 h | 15.413 | Operadores da própria Base — administram usuários, permissões e integrações |
| `superadmin@autochecker.cloud` | 69,5 h | 9.146 | AutoMind (suporte/admin) — único perfil que usa *Integrações* e *Cadastro de veículos/motoristas* |
| `tarcisiosalviano@gmail.com` | 0,5 h | 7 | Conta avulsa, uso residual |

---

## 3. Perfil de cada empresa

**Copercana** — 503 h, 29 dos 30 dias. É a operação de verdade: 1.702 buscas de documentos, 2.006 checagens de cota de upload, 135 uploads. Concentração de risco alta: `administrativodist@` sozinho fez **35.759 requisições (61% da empresa)**. Se essa pessoa sair de férias, o número da Base cai pela metade.

**Rede Petro** — 119 h, 4 usuários, o time mais distribuído da base (8.280 / 3.602 / 3.353 — sem usuário único dominante). Melhor saúde técnica do conjunto: **6 erros em 15.280 requisições**. Usa configuração de notificações de forma intensa (347 req), o que sugere time engajado ajustando o produto ao próprio fluxo.

**Flexpetro** — 84,5 h em 20 dias com **um único usuário** (`faturamentoribeiraopreto@`). Uso constante e solitário: 62 uploads. Cliente saudável, mas com dependência total de uma pessoa.

**Setta Combustíveis** — padrão atípico: 45,5 h concentradas em apenas **6 dias**. Uso em rajada (provavelmente fechamento), não rotina diária. 96,2% de polling — o maior da base, ou seja, deixa a tela aberta muito tempo sem agir.

**Larco Petróleo** — **5,89% de erro, o pior da base** (241 erros). Merece investigação: nenhuma outra empresa passa de 0,82%.

**Biopetro** — único cliente cujo topo é *visualizar documento* (169) acima de listar (150), com 96 etiquetagens e 37 reprocessamentos. Perfil de **conferência/auditoria** de documentos, não de entrada.

**Small** — 38 h em 9 dias, 1 usuário, uso equilibrado entre listar, visualizar e etiquetar.

**GP Combustíveis / Petronac** — as duas únicas empresas cuja função principal é **upload**. São produtoras de documento, não consumidoras. Volume pequeno (23 e 10 uploads), mas o perfil é o inverso do resto da base.

**Midas Combustíveis** — 10,5 h em só 3 dias, e o topo é *consultar processados* (153 req). Entra pontualmente para conferir resultado de lote.

**Argemil Distribuidora / BP** — uso residual (3,5 h e 2,5 h, 2 dias cada). **BP não fez nenhum upload e sua única atividade real foi mexer em configuração de notificação** — perfil de conta nova ou abandonada. Candidatos a ação comercial.

---

## 4. Achados que valem ação

| # | Achado | Por quê importa | Ação sugerida |
|---|--------|-----------------|---------------|
| 1 | **89,5% do tráfego é polling** (109.388 de 122.248 req). Só `unread_count` são ~69 mil. | Custo de infra e ruído puro. Copercana sozinha gera 39.119 `unread_count`. | Trocar polling por *push*/WebSocket ou subir o intervalo. Maior ganho de FinOps disponível hoje. |
| 2 | **Larco com 5,89% de erro** (241 erros/4.091 req), ~7× a média. | Cliente com experiência degradada e ninguém notou. | Cruzar com Sentry e abrir ticket. |
| 3 | **Concentração em pessoa única**: Copercana 61% num usuário; Flexpetro, Small, Setta e Petronac operam com **1 usuário só**. | Risco de continuidade do cliente — férias/desligamento derruba o uso. | Sinalizar ao comercial: ampliar base de usuários nessas contas. |
| 4 | **Só 385 uploads em 30 dias** contra ~98 mil requisições. | O valor central do produto (processar documento) quase não é exercido pela web. | Confirma o ponto cego já mapeado: o volume real entra por **integração/API**, invisível no `api.log`. |
| 5 | **BP e Argemil praticamente inativas**; Midas e Setta usam em rajada. | Sinal precoce de churn. | Régua de ativação por uso. |
| 6 | **`superadmin@autochecker.cloud` gasta 69,5 h dentro do tenant do cliente** | É a AutoMind operando manualmente pelo cliente — 2,54% de erro nessas ações. | Avaliar quanto disso é suporte recorrente que poderia virar autosserviço. |

---

## 5. Empresas em trial

> **Escopo:** os trials rodam em **tenants próprios**, fora da Base Compartilhada. Entram aqui como anexo comercial porque a pergunta "quem está avaliando o AutoChecker" complementa a de "quem está usando".

| Empresa | Tenant | Usuário | Expira | Uploads usados | Última atividade |
|---|---|---|---|---:|---|
| **Tecab** | `tecab_2cf34e0a` | `cadastro@tecab.srv.br` | 02/08/2026 | **0 de 50** | 13/07 (7 dias atrás) |
| **Petroserra** | `petroserra_f7c70c21` | `transportes04@petroserra.com` | **22/07/2026 — em 2 dias** | **1 de 50** | 22/06 (**28 dias atrás**) |

Também aparecem com `is_trial: true` os tenants `automind_2_dc8b63db` e `automind_teste_fcc16395` — contas da própria AutoMind, não prospects.

**Fonte:** a rota `/api/trial/status/` devolve um corpo que fica gravado no `api.log`:
`{"is_trial":"true","days_remaining":"20","days_total":"30","uploads_used":"0","uploads_limit":"50","alert_level":"normal","expiration_date":"2026-08-02"}`

### Os dois trials estão parados

- **Petroserra** entrou em 22/06, fez **1 upload** e nunca mais voltou — 28 dias de silêncio num trial de 30, que vence em 22/07. Vai expirar sem que a empresa tenha experimentado o produto.
- **Tecab** está com **0 uploads em 20 dias**. E no tenant dela a conta da AutoMind (`autochecker.cloud`) fez **1.895 requisições contra 962 do cliente** — quem mais mexeu no trial da Tecab foi a AutoMind, não a Tecab.
- Nenhum dos dois chegou perto do limite de 50 uploads: o gargalo não é o plano, é que ninguém está usando.
- **`provision_trial_tenant_task` teve zero execuções em 30 dias** — mas **dois trials começaram nesse período** (Petroserra em 22/06, Tecab em 03/07). Ou seja, os trials **não nascem por essa task**: estão sendo provisionados por outro caminho, provavelmente manual pelo admin. O funil não está vazio; o que não existe é o fluxo self-service.

### Ação já tomada

**Eduardo notificou a equipe de marketing do AutoChecker sobre a expiração do trial da Petroserra** (20/07/2026). O caso da Tecab (0 uploads, vence 02/08) ainda não tem tratativa registrada.

### ⚠️ Ressalva sobre a atualidade destes números

Os valores vêm da **última vez que alguém abriu o app** — o endpoint só responde quando há acesso. Para a Petroserra, o retrato é de **22/06**; não dá para ver o valor de hoje porque ninguém entrou desde então. O `expiration_date` é fixo e confiável; já `days_remaining` e `uploads_used` são "último observado", não ao vivo.

O `alert_level` estava `normal` nos dois casos. Existe mecanismo de alerta de trial no produto, mas um trial a 2 dias do fim com 1 upload não está sendo escalado por ele — vale checar em que limiar esse campo muda.

---

## 6. Método e limitações — leia antes de citar os números

**Como foi medido.** Query LogQL sobre `job="autochecker-backend"`, `environment="prod"`, filtrando `tenant_schema="base_compartilhada"` e `user_email != ""`. A empresa é derivada do domínio do e-mail via `label_format domain={{ regexReplaceAll "^.*@" .user_email "" }}` — exatamente o agrupamento pedido (soma dos usuários de um mesmo domínio = empresa).

**⚠️ "Tempo de uso" é estimativa, não medição.** O AutoChecker **não registra evento de login/logout nem duração de sessão**. O número aqui é um proxy: contam-se as **janelas de 30 minutos em que a empresa teve pelo menos 1 requisição**, e multiplica-se por 0,5 h. Isso **superestima** quem deixa a aba aberta sem trabalhar (o polling mantém a janela "ativa") e **arredonda para cima** quem entra por 2 minutos. Trate como *ordem de grandeza e ranking*, não como hora cheia faturável. O tempo real de processamento no backend — esse sim medido — está em `duration_ms`: 3.593 s para a Copercana, 992 s para a Rede Petro.

**⚠️ "Ler notificações" foi excluído do topo.** O endpoint `/api/notifications/inbox/` aparecia como função nº 1 em 11 das 15 contas. Ele é chamado junto com o carregamento do sino, não só por ação deliberada — tratá-lo como "função mais usada" seria enganoso. A coluna do ranking usa a maior função **depois** de notificações e polling. Rotas classificadas como polling: `unread_count`, `core/permissions`, `trial/status`, `upload-usage`, `legal/acceptances/status`, `all-tenants-switcher`, `accounts/me`, `site-monitoring`.

**O que este estudo NÃO consegue responder** (lacunas de instrumentação, dependem do dev):
- **Tipo de documento** por empresa — não é logado, só schema + UUID.
- **Tempo de sessão real** — não existe evento de sessão.
- **Uso via mobile/API/integração** — não registra tenant no `api.log`; empresas que processam volume por integração ficam invisíveis aqui.
- **Erros correlacionados ao usuário** — o backend não envia `user.email` ao Sentry.

**Confiabilidade:** `Sei` — requisições, usuários distintos, rotas, uploads, erros, dias ativos. `Parcial` — tempo de uso (proxy), função mais usada (depende da classificação de polling acima). `Não sei` — tipo de documento, uso não-web.

---

## 7. Próximos passos sugeridos

1. **Quantificar o custo do polling** — traduzir os 109 mil requests em R$ de infra. É o argumento mais forte para priorizar a correção.
2. **Investigar os 5,89% de erro da Larco** cruzando com Sentry.
3. **Pedir ao dev 3 instrumentações** que destravam tudo que está em "Não sei": evento de sessão, `document_type` no log, e `tenant` nas chamadas de integração/mobile.
4. **Levar o ranking ao comercial** — concentração em usuário único e contas inativas são conversa de CS, não de engenharia.
5. **Tratar o trial da Tecab** (0 uploads, vence 02/08) — a Petroserra já foi escalada por Eduardo ao marketing em 20/07; a Tecab segue sem tratativa. E entender por que **nenhum trial novo foi provisionado em 30 dias**.
