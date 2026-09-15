# Estudo de Uso de Telas e Funções — AutoChecker · Tenant **Base Compartilhada**

> **Fontes:** Grafana/Loki (logs de produção, janela **7 dias: 06–13/07/2026**) + Sentry `automind-qd` (transações, Session Replay e erros, janela **30 dias: 13/06–13/07/2026**).
> **Identificador de usuário:** e‑mail (`user_email` no Loki; `user.email` no Sentry).
> **Gerado:** 13/07/2026. Regras anti‑alucinação aplicadas — nenhum número sem consulta que o sustente; lacunas marcadas com `[CAMPO AUSENTE]` / `[SEM DADOS]`.

---

## 4.1 Identificação do tenant

| Campo | Valor confirmado | Fonte |
|---|---|---|
| Nome de exibição | **Base Compartilhada** | `tenant.name` no `api.log` |
| `tenant_id` | `a9cdea0f-0b26-4b29-8f7c-65d231ecce1b` | Sentry (tag) + Loki (linha) |
| `schema_name` | `base_compartilhada` | Sentry (tag) + Loki (linha) |
| Período — Loki | 06–13/07/2026 (7 dias) | `{job="autochecker-backend"}` |
| Período — Sentry | 13/06–13/07/2026 (30 dias) | projetos `autochecker-*` |
| Volume de requests (Loki, prod, 7d) | **30.572** | `count_over_time` |

**Notas de método (essenciais para reproduzir):**
- No **Loki** o tenant **não está em label** — o label `tenant` vale sempre `public`. O tenant real está **dentro da linha** JSON (`tenant.schema` / `tenant.name`). A linha do `api.log` vem prefixada por `INFO `, o que quebra `| json`; é preciso `| pattern "<lvl> <js>" | line_format "{{.js}}" | json` antes de filtrar por `tenant_schema="base_compartilhada"`.
- O `api.log` **passou a registrar** `duration_ms` e `user_email` por request (efeito da consolidação de logs de 06/07) — o que **viabiliza** tempo por rota e inferência de sessão, ao contrário do que estudos anteriores supunham.
- Jobs reais no Loki: **`autochecker-backend`** e **`celery-tasks`** (não existe `autochecker-worker`).
- O label `environment` separa `prod` (uso real de cliente) de `dev` (bots varrendo `/api/env/`, `/api/config/`, `/.env`). Todas as métricas abaixo usam `environment="prod"`.

---

## 4.2 Funcionalidades mais utilizadas (ranking)

Agregado por rota → funcionalidade de negócio (Loki, prod, 7d). O retrato dominante é de **tráfego de fundo (polling), não de uso de feature**.

| # | Funcionalidade | Rota(s) principal(is) | Volume 7d | Natureza |
|---|---|---|---:|---|
| 1 | **Notificações** | `/api/notifications/inbox/unread_count/` (16.092) · `/inbox/?page_size=50` (1.208) | **17.300** | polling |
| 2 | **Sessão / Permissões / Conta** | `/api/core/permissions/` (6.602) · `/trial/status/` (1.490) · `/tenants/all-tenants-switcher/` (1.191) · `/legal/acceptances/status/` (520) · `/accounts/me/` (421) | **10.224** | polling / "chrome" |
| 3 | **Documentos — consulta** | `/api/documents/?page…` (740) · `/documents/{uuid}/view/` (~70) · `/documents/processed/` (35) | **~845** | **uso real** |
| 4 | **Documentos — uso/cota** | `/api/documents/upload-usage/` (1.029) | 1.029 | polling |
| 5 | **Documentos — envio** | `/api/documents/upload/multi/` (134) | **134** | **uso real (core)** |
| 6 | **Integrações** | `/api/integrations/providers/` (32) · `/integrations/logs/?…` (21) | 53 | uso real |
| 7 | **Validação / Monitoramento** | `/api/validation/site-monitoring/` | 35 | uso real |
| 8 | **Administração de usuários** | `/api/accounts/users/all_users/` (16) · `/groups/all-groups/` (13) | 29 | uso real |

**Leitura:**
- **Notificações sozinhas = 57%** de todo o tráfego web do tenant, quase inteiramente `unread_count` (16.092 chamadas / 7d ≈ 1 a cada 37s por sessão aberta).
- **Polling + "chrome" de sessão ≈ 84–89%** do tráfego. O **produto de fato (documentos)** — envio, consulta, exclusão — soma cerca de **~2.000 requests (≈6,6%)**, e mesmo assim metade disso é o `upload-usage` (checagem de cota).
- O **envio de documentos** (a ação que gera valor) é apenas **134 requests/semana** na camada web — mas dispara **~2.200 documentos processados** no worker (§4.9). Ou seja: o esforço do usuário é pequeno; o trabalho pesado é do backend.

---

## 4.3 Usuários mais ativos (por e‑mail)

Loki, prod, 7d, ordenado por volume de requests. Contas internas (AutoMind / basecompartilhada.com.br) marcadas — **não são clientes finais**.

| # | E‑mail | Requests 7d | Cliente (domínio) | Obs. |
|---|---|---:|---|---|
| 1 | `fmelo@basecompartilhada.com.br` | 4.229 | — | **interno** |
| 2 | `controladoriadist2@copercana.com.br` | 3.678 | Copercana | maior cliente real |
| 3 | `superadmin@autochecker.cloud` | 2.839 | — | **interno** |
| 4 | `flaviaminhuk@redepetro.com.br` | 2.730 | Rede Petro | |
| 5 | `rvandre@redepetro.com.br` | 2.657 | Rede Petro | power user (ver §4.7) |
| 6 | `janaina.cristina@small.com.br` | 2.134 | Small | |
| 7 | `faturamento@redepetro.com.br` | 1.516 | Rede Petro | |
| 8 | `administrativodist@copercana.com.br` | 1.475 | Copercana | |
| 9 | `faturamentodist2@copercana.com.br` | 1.310 | Copercana | |
| 10 | `faturamentodist@copercana.com.br` | 1.308 | Copercana | |
| 11 | `faturamento1@biopetro.com.br` | 1.208 | Biopetro | |
| 12 | `faturamentobio@biopetro.com.br` | 985 | Biopetro | maior "consultor" (§4.9) |
| 13 | `marcia.galatte@settacombustiveis.com.br` | 973 | Setta | |
| 14 | `regivanio.souza@larcopetroleo.com.br` | 796 | Larco | |
| 15 | `faturamentoribeiraopreto@flexpetro.com` | 718 | Flexpetro | |

**Clientes de negócio identificados dentro da Base Compartilhada** (por domínio de e‑mail, cruzando Loki 7d + Sentry 30d): **Copercana, Rede Petro, Biopetro, Small, Setta, Larco, Flexpetro, Petronac, GP Combustíveis, Midas, Guterres, Argemil, BP** (`carolina.ladeira@bp.com`). Contas internas: `basecompartilhada.com.br`, `autochecker.cloud`, `automind.com.br`.

---

## 4.4 Tempo de uso por usuário (visão geral)

> **Como o tempo foi medido — leia antes de usar os números.** Não existe evento de login/logout no produto, então **não há duração de sessão pronta**. Foram usados **dois proxies independentes**, que se validam mutuamente:
> - **Loki — "app aberto" (primário):** contagem de **janelas de 30 min com atividade** por usuário (o app faz polling contínuo enquanto uma aba está aberta, então uma janela ativa ≈ aba aberta naquela meia‑hora). Cada janela ativa = 30 min. É **tempo com o app aberto**, não necessariamente tempo de interação ativa (abas esquecidas abertas inflam o número).
> - **Sentry — Session Replay (validação):** duração real de sessões gravadas — mas com **amostragem de ~10%** (`replaysSessionSampleRate: 0.1`), então serve para **validar**, não para somar.

**Tempo "app aberto" por usuário (Loki, 7d) — clientes reais, ordenado:**

| # | E‑mail | Cliente | Janelas 30min | Tempo app‑aberto | Requests |
|---|---|---|---:|---:|---:|
| 1 | `flaviaminhuk@redepetro.com.br` | Rede Petro | 57 | **28,5 h** | 2.626 |
| 2 | `janaina.cristina@small.com.br` | Small | 52 | **26,0 h** | 2.134 |
| 3 | `controladoriadist2@copercana.com.br` | Copercana | 51 | **25,5 h** | 3.678 |
| 4 | `rvandre@redepetro.com.br` | Rede Petro | 42 | **21,0 h** | 2.713 |
| 5 | `faturamento@redepetro.com.br` | Rede Petro | 29 | 14,5 h | 1.516 |
| 6 | `administrativodist@copercana.com.br` | Copercana | 23 | 11,5 h | 1.475 |
| 7 | `faturamentodist@copercana.com.br` | Copercana | 20 | 10,0 h | 1.308 |
| 8 | `marcia.galatte@settacombustiveis.com.br` | Setta | 20 | 10,0 h | 973 |
| 9 | `faturamento1@biopetro.com.br` | Biopetro | 19 | 9,5 h | 1.208 |
| 10 | `faturamentoribeiraopreto@flexpetro.com` | Flexpetro | 16 | 8,0 h | 723 |

**Tempo "app aberto" agregado por cliente (Loki, 7d):**

| Cliente | Tempo app‑aberto | Requests 7d |
|---|---:|---:|
| **Rede Petro** | **64,0 h** | 6.855 |
| **Copercana** | **55,5 h** | 8.302 |
| Small | 26,0 h | 2.134 |
| Biopetro | 14,0 h | 2.193 |
| Setta | 10,0 h | 973 |
| Flexpetro | 8,0 h | 723 |
| Larco | 4,0 h | 796 |
| Petronac | 3,0 h | 181 |
| GP Combustíveis | 1,5 h | 141 |
| Midas | 1,0 h | 184 |

**Validação por Session Replay (Sentry, 30d):** as durações reais gravadas confirmam a ordem acima — `rvandre@redepetro` aparece com sessões de **92 min, 30 min, 25 min e 21 min** (o maior tempo de tela do tenant), e `faturamento@redepetro` com 6 min. Sessões reais de clientes vão de ~5 min a ~92 min. A convergência Loki↔Replay dá confiança ao proxy.

---

## 4.5 Tempo de uso por funcionalidade (tempo de servidor por rota)

> **Atenção ao rótulo:** aqui o "tempo" é **`duration_ms` = tempo de processamento no servidor** (quanto o backend levou para responder), somado na janela — **não é tempo do usuário na tela**. É útil para achar **rotas lentas / caras**, não engajamento.

| Rota / Tela | Chamadas 7d | Tempo servidor total | Tempo médio | Observação |
|---|---:|---:|---:|---|
| `/api/tenants/all-tenants-switcher/` | 1.191 | 544 s | ~457 ms | pesada p/ multi‑empresa |
| `/api/documents/?page_size=1000` | 19 | 425 s | **~22 s/chamada** | **listagem sem paginação — crítica** |
| `/api/documents/?page=1&page_size=10` | 680 | 322 s | ~474 ms | listagem padrão |
| `/api/notifications/inbox/unread_count/` | 16.092 | 304 s | ~19 ms | rápida, mas volume gigante |
| `/api/core/permissions/` | 6.602 | 213 s | ~32 ms | polling |
| `/api/documents/upload/multi/` | 134 | 108 s | ~805 ms | envio (esperado ser mais lento) |
| `/api/documents/upload-usage/` | 1.029 | 50 s | ~49 ms | polling de cota |
| `/api/trial/status/` | 1.490 | 48 s | ~32 ms | polling |

**Leitura:** `/api/documents/?page_size=1000` é o maior ofensor por chamada (~22 s) — listagem sem paginação que puxa o histórico inteiro; candidata nº 1 a otimização. O `all-tenants-switcher` é caro por ser multi‑empresa (a Base carrega a lista de todos os sub‑clientes a cada troca).

### 4.5b Engajamento por funcionalidade × usuário — quem realmente opera documentos

Como o log **não registra tempo de interação por tela** (só `duration_ms` de servidor), o proxy honesto de engajamento é a **contagem de ações reais** por usuário. Duas ações que representam o núcleo do produto:

**Envios de documento (`POST /upload/multi/`, 7d) — clientes:**

| E‑mail | Cliente | Uploads 7d |
|---|---|---:|
| `controladoriadist2@copercana.com.br` | Copercana | **29** |
| `rvandre@redepetro.com.br` | Rede Petro | 13 |
| `faturamentoribeiraopreto@flexpetro.com` | Flexpetro | 13 |
| `flaviaminhuk@redepetro.com.br` | Rede Petro | 13 |
| `faturamentodist4@copercana.com.br` | Copercana | 10 |
| `faturamento@redepetro.com.br` / `faturamentobio@biopetro.com.br` | RedePetro / Biopetro | 8 cada |
| `jpedro@petronac.com.br` · `marcia.galatte@setta` · `faturamento1@biopetro` | Petronac/Setta/Biopetro | 6 cada |

**Visualizações de documento (`/documents/{uuid}/view/`, 7d) — clientes:**

| E‑mail | Cliente | Views 7d |
|---|---|---:|
| `faturamentobio@biopetro.com.br` | Biopetro | **74** |
| `faturamento1@biopetro.com.br` | Biopetro | 32 |
| `rvandre@redepetro.com.br` | Rede Petro | 20 |
| `administrativodist@copercana.com.br` | Copercana | 18 |
| `controladoriadist2@copercana.com.br` | Copercana | 18 |
| `janaina.cristina@small.com.br` | Small | 16 |

**Leitura:** o perfil difere por cliente — **Copercana (controladoriadist2)** é o maior **enviador**; **Biopetro (faturamentobio)** é o maior **conferente/leitor** de documentos. Rede Petro faz os dois em volume alto.

---

## 4.6 Erros por usuário e funcionalidade

Sentry, projeto `autochecker-backend`, `schema_name:base_compartilhada`, 30d.

| E‑mail | Erro | Volume | Funcionalidade afetada |
|---|---|---:|---|
| `[CAMPO AUSENTE]` (user.email = null) | *sem tipo definido* | 60 | não atribuível |
| `[CAMPO AUSENTE]` | `ImportError` | 6 | inicialização / deploy |
| `[CAMPO AUSENTE]` | `User.DoesNotExist` / `UniqueViolation` / `IntegrityError` | 3 | cadastro / conta |

**Leitura:** o Base Compartilhada é **estável** — apenas ~69 eventos de erro em 30 dias para o maior tenant do produto. **Nenhum erro traz `user.email`** (o backend não popula o usuário no evento de erro) → não é possível atribuir erro a cliente pelo Sentry. `[CAMPO AUSENTE — user.email nos erros backend]`.

---

## 4.7 Padrão de comportamento (Session Replay)

Do Sentry Session Replay (30d, amostra ~10%), evidências qualitativas de **como** os clientes usam:
- **`rvandre@redepetro.com.br`** é o power user do tenant: sessão contínua de **1h32min** (35+ páginas navegadas), além de várias de 20–30 min. Chrome desktop.
- Uso **mobile real existe**: `cadastro@tecab.srv.br` (10 min, Samsung Internet) e sessões via Mobile Safari em `/tenant/upload` — confirma que parte da operação é feita pelo celular.
- **Telas mais presentes nos replays:** `/tenant/home`, `/tenant/documents`, `/tenant/upload`, `/login`.
- Qualidade de UX boa: quase **zero rage clicks**; poucos dead clicks isolados.

**Tempo de carga de tela (Sentry transactions, 30d — projeto todo, ~85% Base):**

| Tela | Carga média |
|---|---:|
| `/tenant/home` | 1,65 s |
| `/tenant/documents` | 1,45 s |
| `/tenant/settings` | 1,26 s |
| `/tenant/upload` | 1,11 s |
| `GET /api/document/list-paged` | 1,07 s |
| `GET /api/permission/get` | 0,76 s |

---

## 4.8 Lacunas encontradas

- `[CAMPO AUSENTE — user no worker]` — os logs do `celery-tasks` **não têm e‑mail nem user_id**; só o schema do tenant no `args_summary`. **Documentos processados por usuário é impossível** hoje via worker.
- `[CAMPO AUSENTE — user.email nos erros backend]` — eventos de erro do Sentry não trazem o usuário → erro não é atribuível a cliente.
- `[CAMPO AUSENTE — document_type]` — o tipo de documento (CT‑e, NF‑e, MDF‑e, etc.) **não é logado** (só schema + UUID). "Tipos de documento por cliente" continua impossível.
- `[CAMPO AUSENTE — evento de sessão]` — sem login/logout; tempo de uso é **proxy** (janelas ativas / replay amostrado), não medição direta.
- **Frontend não filtrável por tenant de forma limpa** — a tag de tenant não está confiável nas transações; ~196 mil transações vêm com `user.email = null`. Os números de transação/carga do Sentry são do **projeto inteiro** (~85% Base), não só do tenant.
- **Retenção do Loki ≈ 7 dias** efetivos — não dá para comparar mês a mês pelos logs; séries longas só via Sentry (30d) ou dashboard fixo.
- **Ponto cego de integração/API** — clientes que operam por integração/mobile podem não gerar `user_email` no `api.log`; a camada web sub‑representa quem processa via API.

---

## 4.9 Volume de documentos processados (worker)

`celery-tasks`, filtrado por `base_compartilhada`, 7d, por tipo de task:

| Etapa do pipeline | Task | Iniciadas 7d | Falhas |
|---|---|---:|---:|
| Autenticação | `authenticator.authenticate_document` | 5.917 | 2 |
| Classificação | `classification.classify_document` | 2.417 | 72 |
| Extração | `extract.extract_data` | 2.269 | 75 |
| OCR (Textract) | `ocr.run_textract` | 2.208 | 4 |
| Reprocessamento | `reprocess.reprocess_document(s)` | 455 | 57 |
| Notificações | `notification_tasks.process_notification_task` | 30.423 | — |

**Leitura:** tomando classificação/extração/OCR como proxy de "1 por documento", o Base Compartilhada processou **~2.200 documentos na semana**. A maior carga do worker, porém, é **notificação (30.423 tasks)** — o mesmo padrão de fundo visto na camada web. Taxa de falha do pipeline documental é baixa (**~3%**).

---

## 4.10 Recomendações de instrumentação futura

1. **Logar `user_email`/`user_id` no worker** (`celery-tasks`) — desbloqueia "documentos processados por cliente/usuário", hoje impossível.
2. **Logar `document_type`** no pipeline de validação — desbloqueia "quais tipos de documento cada cliente processa" (pergunta recorrente do negócio).
3. **Emitir evento de sessão** (login/logout ou heartbeat de foco) — substitui os proxies por medição real de tempo de uso.
4. **Popular `user` nos eventos de erro do backend** (`Sentry.set_user` no middleware) — permite atribuir erro a cliente.
5. **Enviar tag `tenant` confiável nas transações do frontend** — permite recortar performance/uso por cliente no Sentry.
6. **Otimizar `/api/documents/?page_size=1000`** (~22 s/chamada) e reduzir a frequência do polling de `unread_count`/`permissions` (57%+ do tráfego) — ganho direto de custo e de latência percebida.
7. **Consolidar num dashboard fixo no Grafana** (uso por cliente, tempo app‑aberto, uploads/views por usuário) para superar a retenção de 7 dias do Loki.

---
*Dados ao vivo em 13/07/2026. Loki `monitor.autochecker.cloud` (7d) + Sentry `automind-qd` (30d). E‑mails são dado pessoal (LGPD) — uso interno restrito à observabilidade; ver auditoria LGPD dos logs (10/07).*
