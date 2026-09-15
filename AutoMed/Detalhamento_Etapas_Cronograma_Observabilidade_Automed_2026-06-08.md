# Detalhamento das Etapas — Cronograma de Observabilidade · Automed

> **O que é este documento:** o desdobramento item a item das **29 etapas** do cronograma de observabilidade do Automed. Para cada etapa, reúne os campos do cronograma (camada, esforço, semanas, responsável, status), a descrição técnica, a evidência no Sentry/doc que a justifica, as dependências e o critério de "pronto".
>
> **Produto:** Automed · **Ferramenta central:** Sentry (org `automind-qd`, projeto `automed`) · **Data-base:** 08/06/2026.
>
> **Fontes (cruzadas):**
> - `Cronograma_Observabilidade_Automed_2026-06-08.xlsx/.html/.pdf` (cronograma — 7 ondas, 29 itens)
> - `Contexto_Observabilidade_Automed_2026-06-08.md` (contexto de implantação)
> - Snapshot Sentry do projeto `automed` (janela 01→07/06/2026, 18 issues) + doc técnica + estudo estático 14/04/2026.

---

## Como ler este documento

### Estrutura em 7 ondas

| Onda | Semanas | Foco | Itens | "Pronto" quando… |
|---|---|---|---|---|
| **0 — Saneamento da Base** | 1–2 | environment, release, schema drift, migração por organização, ruído de host, domínio, PII, triagem | 1–8 | base limpa: ≥99% com `environment` correto; ruído dominante (~470 ev) eliminado; 0 issues sem status |
| **1 — Fundação dos SDKs e Cobertura** | 3–4 | tags de tenant, cobertura dos 3 Workers, Frontend Angular, política de envio | 9–12 | Workers e Frontend instrumentados; organização em todo evento |
| **2 — Contexto e Agrupamento** | 4–6 | instrumentar sync, capturar excepts silenciosos, fingerprint de cálculo | 13–15 | sync rastreável por unidade/dia; excepts dos Workers no Sentry |
| **3 — Alertas + Health Checks** | 6–8 | N1/N2/N3, regras por ambiente, /health+uptime, cron monitors, canal | 16–20 | alertas acionáveis chegando ao N1; 3 Workers com cron monitor |
| **4 — Performance + Logs** | 8–10 | timeouts SQL, tracing API↔Workers, centralizar logs | 21–23 | trace API↔Worker + salto erro↔log |
| **5 — Métricas + Dashboard** | 10–12 | métricas de negócio, dashboard por organização/fluxo | 24–25 | dashboard por organização/fluxo exibível |
| **6 — Endurecimento + Regulatório** | 12–14 | rastreabilidade ANP, conectividade XConnect/PI, desvios, segurança | 26–29 | rejeição/prazo ANP alertados; conectividade por organização monitorada |

> **Onda 0 é um GATE:** nenhuma ampliação (alertas, tracing, métricas) começa antes de o saneamento estar concluído.

### Legendas

- **Esforço:** `P` ≤ 1 dia · `M` = 2–5 dias · `G` > 5 dias.
- **Semanas:** relativas (Sem 1..14). A âncora de calendário (qual é a Semana 1) ainda **não está definida nas fontes**.
- **Responsável (todos):** **"A definir"** — equipe ainda não atribuída por item.
- **Status (todos):** **Não iniciado** (cronograma criado em 08/06/2026).
- **Janela Sentry:** as contagens de evento referem-se a **01→07/06/2026** (7 dias).

### Quadro-resumo das 29 etapas

| # | Onda | Etapa | Camada | Esf. | Semanas | Evidência-chave |
|---|---|---|---|---|---|---|
| 1 | 0 | Padronizar `environment` + isolar DEV/QA/HOMOLOG/PRD | API | M | Sem 1 | 1 só env (`production`) |
| 2 | 0 | Padronizar `release` (AppVersion) + associar a deploy | API | M | Sem 1 | 2 agentes Azure publicando |
| 3 | 0 | Corrigir schema drift de colunas (`AceitoUsuario`, `enviado`) | Models/DB | M | Sem 1–2 | AUTOMED-Z/10/Y ~247 ev |
| 4 | 0 | Aplicar migrações faltantes por schema de organização | Models/DB | M | Sem 1–2 | AUTOMED-A/2 ~71 ev |
| 5 | 0 | Filtrar/corrigir ruído de host (`https port`) | API | P | Sem 2 | AUTOMED-1 107 ev |
| 6 | 0 | Reclassificar exceções de domínio (auth+validação) | API | M | Sem 2 | AUTOMED-5/G/V/T/B/X/W |
| 7 | 0 | Confirmar `SendDefaultPii=false` + scrubbing PII | API/Frontend | M | Sem 2 | setUser(email); ConnString |
| 8 | 0 | Triagem ZERO do backlog (18 issues) | Automed | M | Sem 2 | 18 unresolved, 0 resolvidas |
| 9 | 1 | Tags de tenant na API (`organizacao_id`, `usuario_id`) | API | M | Sem 3–4 | userCount=1 em tudo |
| 10 | 1 | Estender Sentry aos 3 Workers | Workers | G | Sem 3–4 | logs no Event Viewer |
| 11 | 1 | Instrumentar o Frontend Angular 13 | Frontend | M | Sem 3–4 | sem projeto de frontend |
| 12 | 1 | Política de envio por camada/ambiente | Automed | P | Sem 4 | espelha AutoLoad/AutoChecker |
| 13 | 2 | Instrumentar pipeline de Sync (XConnect/PI/Scan) | Sync.Worker | G | Sem 4–5 | estudo #5 (ProducoesService) |
| 14 | 2 | Capturar erros silenciosos nos Workers | Workers | M | Sem 5–6 | estudo #3/#4 (catch LogError) |
| 15 | 2 | Fingerprint dos erros de cálculo de produção | Tasks.Worker | M | Sem 5–6 | AUTOMED-6 55 + AUTOMED-S 20 |
| 16 | 3 | Definir N1/N2/N3 e responsáveis | Automed | M | Sem 6 | gate da política de alertas |
| 17 | 3 | Regras de alerta com `environment:production` | Automed | M | Sem 6–7 | `automed` fora de qualquer regra |
| 18 | 3 | Health Check `/health` + Uptime Monitor | API | M | Sem 7 | estudo #9 (sem /health) |
| 19 | 3 | Cron Monitors para os 3 Workers | Workers | M | Sem 7–8 | estudo #8; hasMonitors=False |
| 20 | 3 | Integração de alertas em canal + ticket + CODEOWNERS | Automed | M | Sem 8 | só e-mail genérico no org |
| 21 | 4 | Timeouts de SQL + performance nos endpoints | API | M | Sem 8–9 | AUTOMED-7/4 (timeout) |
| 22 | 4 | Tracing API ↔ Workers (Refit) | Automed | M | Sem 9–10 | workers via Refit+JWT |
| 23 | 4 | Centralizar logs dos Workers + correlação | Workers | G | Sem 9–10 | Event Viewer, sem agregação |
| 24 | 5 | Definir métricas de negócio | Automed | M | Sem 10–11 | produção/ANP/tarefas |
| 25 | 5 | Dashboard por organização e por fluxo | Automed | G | Sem 11–12 | Sync→Tasks→ANP |
| 26 | 6 | Rastreabilidade do fluxo ANP | Tasks.Worker | M | Sem 12 | AUTOMED-C/X/B |
| 27 | 6 | Monitorar conectividade XConnect/PI por organização | Sync.Worker | M | Sem 12–13 | estudo #6 (ConnectionString) |
| 28 | 6 | Rastrear desvios de medição + importação ANP | Tasks.Worker | M | Sem 13 | estudo #7/#10 |
| 29 | 6 | Endurecimento de segurança (brute-force, CORS) | API | M | Sem 13–14 | estudo #12; AUTOMED-5 |

---

# ONDA 0 — Saneamento da Base (Semanas 1–2)

> 🔴 **GATE: nada de ampliação antes disto.** Os maiores ofensores de hoje são **bugs de versão de banco** (colunas e tabelas que o código espera mas não existem em produção/em alguns schemas) e **ruído de configuração de host** — juntos, mais de 470 eventos na semana que escondem incidentes reais.

---

## Etapa 1 — Padronizar `environment` + isolar DEV/QA/HOMOLOG/PRD

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 1 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** o projeto `automed` no Sentry tem **um único `environment`: `production`**. O produto tem LOCAL/DEVELOPMENT/QA/HOMOLOG (TAF/TAC)/PRODUCTION (seção `Ambientes` do `appsettings`), mas ou esses ambientes não enviam ao Sentry ou caem todos como `production`. Configurar `options.Environment` a partir de `ASPNETCORE_ENVIRONMENT`/config e garantir que só PRD popule o projeto produtivo.

**Evidência:** `project.environments = ['production']` (snapshot Sentry).

**Dependência / papel no plano:** é o **gate de tudo que mede produção** — alertas e dashboards ficam contaminados enquanto o `environment` estiver achatado.

**Critério de pronto (KPI):** **≥99% dos eventos com `environment` correto em 7 dias**, com QA/HOMOLOG isolados.

---

## Etapa 2 — Padronizar `release` (AppVersion) + associar a deploy/commits

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 1 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** definir `options.Release = AppVersion` consistente na API (e depois Workers/Frontend) e associar o release ao deploy para habilitar **suspect commits** e correlação **picos × deploy**.

**Evidência:** o estudo prevê `Sentry:Release = #{AppVersion}#`. Os stacktraces mostram **dois agentes de build do Azure DevOps** coexistindo (`D:\Agents\DevopsService\AgentBuild1\...` e `AgentBuild2\...`) — sinal de mais de um agente/branch publicando; sem release consistente não se sabe qual versão gerou cada erro.

**Critério de pronto:** `release` padronizado e associado ao deploy; erros passam a exibir a versão de origem.

---

## Etapa 3 — Corrigir schema drift de colunas (`AceitoUsuario`, `enviado`)

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | Models / DB |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 1 – Sem 2 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** **maior cluster da semana.** O código referencia colunas que **não existem no banco**:
- `SqlException: Invalid column name 'AceitoUsuario'` em `Sql.FetchAll` (**AUTOMED-Z, 185 ev**);
- `KeyNotFoundException: 'aceitoUsuario'` em `NotificacaoDAL.RowToNotificacao` (**AUTOMED-10, 57 ev**) — o mesmo campo, do lado do mapeamento Row→objeto;
- `SqlException: Invalid column name 'enviado'` em `Sql.Execute` (**AUTOMED-Y, 5 ev**).

Causa típica: **código publicado à frente da migração EF Core** (ou migração não aplicada em produção). Alinhar migração × deploy e adicionar um **gate** que falha o deploy se houver migração pendente.

**Evidência:** AUTOMED-Z 185 + AUTOMED-10 57 + AUTOMED-Y 5 ≈ **247 ev** — a maior fonte de ruído do produto.

**Critério de pronto:** colunas presentes no banco em todos os ambientes/organizações; cessação dos `Invalid column name`/`KeyNotFound`. **Bug corrigível que remove a maior parte do ruído.**

---

## Etapa 4 — Aplicar migrações faltantes nos schemas por organização

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | Models / DB |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 1 – Sem 2 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** `SqlException: Invalid object name '<hash>.monitoramentos'` em `Sql.Execute` (**AUTOMED-A 47 ev + AUTOMED-2 24 ev**): a tabela `monitoramentos` **não existe em um schema de organização** (ex.: `db5cd138903b59527ee0c4840913c0b8`). O Automed é multi-tenant com **schema por organização** — a migração **não chegou a esse schema**. Garantir que o deploy aplique as migrações a **todos** os schemas de organização (análogo ao `migrate_schemas` do AutoChecker) e adicionar verificação por organização.

**Evidência:** AUTOMED-A 47 + AUTOMED-2 24 = **71 ev**. O nome do objeto com hash confirma o isolamento por schema de organização.

**Critério de pronto:** todas as organizações com as tabelas esperadas; cessação dos `Invalid object name`. **Bug corrigível que remove grande parte do ruído residual.**

---

## Etapa 5 — Filtrar/corrigir ruído de host (`Cannot determine the https port`)

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | API |
| **Esforço** | P (≤ 1 dia) |
| **Semanas** | Sem 2 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** maior issue **único** por volume: `InvalidOperationException: Cannot determine the https port from IServerAddressesFeature` no `HttpsRedirectionMiddleware` (**AUTOMED-1, 107 ev**). É erro de **configuração de hosting** (porta HTTPS não resolvida atrás do proxy/Kestrel). Resolver configurando a porta HTTPS (`UseHttpsRedirection`/`ForwardedHeaders`/`ASPNETCORE_HTTPS_PORT`) ou, se for esperado atrás de um proxy que termina o TLS, **descartar via `before_send`/Inbound Filter**.

**Evidência:** AUTOMED-1 107 ev — ruído de infra mascarando o sinal.

**Critério de pronto:** issue cessada (corrigida) ou filtrada; deixa de figurar entre os maiores volumes.

---

## Etapa 6 — Reclassificar exceções de domínio esperadas (auth + validação)

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 2 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** várias `AutomedException` **previstas** estão sendo capturadas como `error` e inflando o ruído:
- `UsuarioSendoUtilizado (Unauthorized)` no `AuthController.Login` (**AUTOMED-5, 49 ev**);
- `EventoNaoExistente (Forbidden)` em `ExcluirEvento` (**AUTOMED-G**);
- `UsuarioInvalido (Forbidden)` em `ReiniciarSenha` (**AUTOMED-V**);
- validações de negócio: `duas aberturas/fechamentos consecutivos` (**AUTOMED-T**), `BSWFiscal já cadastrado` (**AUTOMED-B**), `BTP já enviado` (**AUTOMED-X**), `Computador de Vazão não cadastrado` (**AUTOMED-W**).

Definir **o que é erro vs evento esperado** e ajustar o nível (`warning`) ou descartar via `before_send`. As de impacto regulatório (B/X) viram **warning de negócio**, não `error` — mas continuam rastreáveis (ver Etapa 26).

**Evidência:** AUTOMED-5 49 ev + G/V/T/B/X/W — `AutomedException` de fluxo esperado tratada como `error`.

**Critério de pronto:** exceções de domínio esperadas em `warning`/drop; nível de erro reservado a falhas inesperadas.

---

## Etapa 7 — Confirmar `SendDefaultPii=false` + scrubbing de PII/LGPD

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | API / Frontend |
| **Esforço** | M (2–5 dias) |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** o estudo propõe `options.SendDefaultPii = false` (item 1) e `Sentry.setUser({email, organizacao})` no frontend (item 2). **Confirmar** que a API não envia PII por padrão; definir scrubbing de e-mail/dados de organização e de qualquer dado sensível de produção (cliente óleo & gás). **Nunca** enviar a `ConnectionString` do XConnect aos eventos/breadcrumbs.

**Evidência:** estudo #1/#2 (`setUser(email)`); nota crítica dos itens #5/#6: a `ConnectionString` por organização é dado sensível.

**Critério de pronto:** `SendDefaultPii=false` confirmado; regras de scrubbing ativas; garantia de que credenciais de banco do cliente nunca trafegam ao Sentry.

---

## Etapa 8 — Triagem ZERO do backlog (18 issues)

| Campo | Valor |
|---|---|
| **Onda** | 0 — Saneamento |
| **Camada** | Automed (transversal) |
| **Esforço** | M (2–5 dias) |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** classificar **todas** as issues (Resolved / Ignored com prazo / In Progress) e documentar o critério. Hoje há **18 abertas e 0 resolvidas** na janela.

**Evidência:** 18 unresolved, 0 resolvidas (Sentry, 01–07/06). Backlog sem dono contamina qualquer métrica derivada.

**Critério de pronto:** 0 issues sem status; critério de triagem documentado.

---

# ONDA 1 — Fundação dos SDKs e Cobertura (Semanas 3–4)

> Sobre a base saneada, dar contexto de tenant aos eventos e — ponto central desta onda — **estender o Sentry aos componentes cegos** (3 Workers + Frontend Angular). "Pronto" quando Workers e Frontend estiverem instrumentados e a organização aparecer em todo evento.

---

## Etapa 9 — Enriquecer contexto/tags na API (`organizacao_id`, `usuario_id`)

| Campo | Valor |
|---|---|
| **Onda** | 1 — Fundação e Cobertura |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 3 – Sem 4 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** adicionar tags globais de tenant no middleware de auth/`BaseController` a partir das claims do JWT — `organizacao_id`, `organizacao_nome`, `usuario_id`. Hoje **todas** as 18 issues mostram `userCount=1`, sinal de que o contexto de usuário/organização não está populado → não se sabe **qual cliente** foi afetado.

**Evidência:** estudo item #2; `userCount=1` em todas as issues (Sentry).

**Critério de pronto:** todo erro identifica a organização afetada; `userCount` passa a refletir usuários reais.

---

## Etapa 10 — Estender Sentry aos 3 Workers (Sync, Tasks, FileExporter)

| Campo | Valor |
|---|---|
| **Onda** | 1 — Fundação e Cobertura |
| **Camada** | Workers |
| **Esforço** | **G (> 5 dias)** |
| **Semanas** | Sem 3 – Sem 4 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** a doc indica que os Workers logam no **Windows Event Viewer**, não no Sentry — porém alguns erros de processos do `Tasks.Core` **já aparecem** (`Automind.Automed.Tasks.Core\Processos\...`). **Confirmar e completar** a cobertura dos 3 Windows Services:
- **Sync.Worker** (orquestra XConnect / PI System / Scan);
- **Tasks.Worker** (fila no banco a cada 5s);
- **FileExporter.Worker** (diário).

Os Workers são **"a fonte principal de erros operacionais"** — sem eles no Sentry, uma falha de sync ou de envio ANP some.

**Evidência:** doc (logs no Event Viewer); Sentry mostra erros do `Tasks.Core`, mas Sync/PI/Scan/FileExporter **a confirmar**.

**Dependência crítica:** pré-requisito da instrumentação do pipeline (Etapa 13) e dos cron monitors (Etapa 19).

**Critério de pronto:** os 3 Workers enviando exceções ao Sentry com tags de worker/organização; cobertura mapeada e documentada.

---

## Etapa 11 — Instrumentar o Frontend Angular 13

| Campo | Valor |
|---|---|
| **Onda** | 1 — Fundação e Cobertura |
| **Camada** | Frontend |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 3 – Sem 4 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** não existe projeto Sentry de frontend (só `automed` dotnet-aspnetcore) — o SPA Angular 13 está **cego**. Instalar `@sentry/angular`, `init` no `main.ts` (environment/release), **`ErrorHandler` customizado** (capturar erros Angular, não só HTTP) e decidir **projeto Sentry próprio** (`automed-frontend`) vs tag. Avaliar Session Replay com masking (PII).

**Evidência:** estudo item #1 (`npm install @sentry/angular`); nenhum projeto de frontend no org.

**Nota:** o estudo lembra que o `@sentry/angular` na versão 13 precisa do `ErrorHandler` customizado para capturar erros Angular além dos HTTP.

**Critério de pronto:** erros do frontend chegando ao Sentry com environment/release; `ErrorHandler` ativo.

---

## Etapa 12 — Documentar política de envio de eventos por camada/ambiente

| Campo | Valor |
|---|---|
| **Onda** | 1 — Fundação e Cobertura |
| **Camada** | Automed (transversal) |
| **Esforço** | P (≤ 1 dia) |
| **Semanas** | Sem 4 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** critério de captura por camada (API/Workers/Frontend) e **nível mínimo por ambiente** (DEV info+debug, QA/HOMOLOG info+warning+error, PRD warning+error). Definir o que é erro vs evento de negócio esperado.

**Evidência / racional:** espelha a política do AutoLoad/AutoChecker; é a base para a reclassificação de ruído (Etapa 6) e para o tratamento do regulatório (Etapa 26).

**Critério de pronto:** política documentada e referenciável pelas etapas de reclassificação.

---

# ONDA 2 — Contexto e Agrupamento (Semanas 4–6)

> Instrumentar o **fluxo central do produto** (sync de produção), fazer os `except` silenciosos dos Workers chegarem ao Sentry e dar fingerprint útil aos erros de cálculo de alta recorrência. "Pronto" quando o sync for rastreável por unidade/dia e os excepts de domínio aparecerem.

---

## Etapa 13 — Instrumentar o pipeline de Sync de produção (XConnect/PI/Scan)

| Campo | Valor |
|---|---|
| **Onda** | 2 — Contexto e Agrupamento |
| **Camada** | Sync.Worker |
| **Esforço** | **G (> 5 dias)** |
| **Semanas** | Sem 4 – Sem 5 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** `ProducoesService` é o coração do produto: lê produção do banco do cliente (XConnect/Weatherford), processa medidores por equipamento e cria eventos de produção. Adicionar tags `sync.unidade_id`/`unidade_nome`/`organizacao_id` e **breadcrumbs por unidade e por dia processado** (qtd de equipamentos) para saber **qual unidade, qual dia** e quantos equipamentos antes de uma falha. Estender ao **PI System** (PlotValues, valores congelados/inválidos) e ao **Scan** (CSV OMNI70/711/712).

**Evidência:** estudo item #5 (`ProducoesService.Executar()`). Falha de sync = **perda de dado de medição (regulatório)**.

**Dependência:** depende da cobertura do Sync.Worker (Etapa 10).

**Critério de pronto:** qualquer falha de sync mostra unidade, dia de produção e equipamentos processados antes da falha.

---

## Etapa 14 — Capturar erros silenciosos nos Workers

| Campo | Valor |
|---|---|
| **Onda** | 2 — Contexto e Agrupamento |
| **Camada** | Workers |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 5 – Sem 6 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** os loops dos Workers capturam exceções com `Logger.LogError()` **sem re-lançar nem enviar ao Sentry** — falha de sync com o XConnect ou de tarefa crítica (`AtualizarSemaforos`, `ProgramarNotificarDesviosMedicaoAdmin`) some silenciosamente. Adicionar `SentrySdk.CaptureException` nos `catch` do **Sync.Worker** (`Worker.cs` ~linhas 39–49) e do **Tasks.Worker** (`Worker.cs` ~linhas 39–42), com tags `worker`/`tarefa`/`organizacao_id`.

**Evidência:** estudo itens #3 e #4 (`Worker.cs` — `catch` com `LogError` sem `capture`).

**Critério de pronto:** falhas de sync e de tarefas de manutenção geram alerta no Sentry com contexto.

---

## Etapa 15 — Fingerprint + tratamento dos erros recorrentes de cálculo de produção

| Campo | Valor |
|---|---|
| **Onda** | 2 — Contexto e Agrupamento |
| **Camada** | Tasks.Worker |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 5 – Sem 6 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** erros de cálculo do `Tasks.Worker` com alto volume e provável causa de **configuração faltante por organização**:
- `Formula para rateio de óleo não cadastrada` em `Calculadores.CalcularProducaoPocos` (**AUTOMED-6, 55 ev**);
- `Estado de operação do poço ... indefinido` em `Calculadores.CalcularTempoOperacaoPoco` (**AUTOMED-S, 20 ev**).

Agrupar por organização/unidade via **fingerprint estável** e **decidir**: é erro de aplicação ou configuração pendente do cliente (vira **warning/alerta de config**)?

**Evidência:** AUTOMED-6 55 + AUTOMED-S 20 (Sentry). Alta recorrência; precisa de fingerprint por unidade + decisão config × erro.

**Critério de pronto:** issues de cálculo agrupadas por causa/unidade; classificação config-vs-erro definida.

---

# ONDA 3 — Alertas + Health Checks (Semanas 6–8)

> Tornar a detecção **proativa**: definir quem recebe o quê (N1/N2/N3 — gate), criar regras por ambiente (hoje **zero** para o Automed), garantir `/health`+uptime e **cron monitors dos 3 Workers**, e plugar tudo num canal que o suporte recebe.

---

## Etapa 16 — Definir níveis N1/N2/N3 e responsáveis por alerta

| Campo | Valor |
|---|---|
| **Onda** | 3 — Alertas + Health Checks |
| **Camada** | Automed (transversal) |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 6 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** mapear **quem recebe qual alerta por nível ANTES** de ativar qualquer notificação. **Gate** da política de alertas. Considerar a **criticidade regulatória (ANP)** na priorização.

**Evidência / racional:** pré-requisito da ativação dos alertas (espelha AutoLoad/AutoChecker). O mapeamento ainda não existe nas fontes.

**Critério de pronto:** mapa N1/N2/N3 definido, com responsáveis por nível.

---

## Etapa 17 — Configurar regras de alerta com filtro `environment:production`

| Campo | Valor |
|---|---|
| **Onda** | 3 — Alertas + Health Checks |
| **Camada** | Automed (transversal) |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 6 – Sem 7 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** hoje o projeto `automed` **não está em nenhuma regra de alerta** — a única regra high-priority do org cobre `autoloadv4-edgegateway` e os projetos do AutoChecker. Criar regras com **filtro `environment:production`**, threshold, ciclo de supressão, **alerta de regressão** (`resolved→unresolved`) e **roteamento por nível** N1/N2/N3.

**Evidência:** `combined_rules` — `automed` ausente da lista de projetos da regra (Sentry).

**Dependência:** depende do `environment` saneado (Etapa 1).

**Critério de pronto:** regras por `environment:production` ativas, com threshold, supressão, regressão e roteamento.

---

## Etapa 18 — Health Check endpoint (`/health`) + Uptime Monitor

| Campo | Valor |
|---|---|
| **Onda** | 3 — Alertas + Health Checks |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 7 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** não existe endpoint `/health` na API → não há como configurar o **Uptime Monitor** do Sentry. Adicionar `AddHealthChecks().AddSqlServer(...)` + check de status dos Workers e `MapHealthChecks('/health')`; configurar Uptime Monitor sobre ele para detectar a API fora do ar **antes do cliente**.

**Evidência:** estudo item #9 (sem `/health` hoje).

**Critério de pronto:** `/health` retornando SQL + status dos Workers; Uptime Monitor ativo.

---

## Etapa 19 — Cron Monitors (check-ins) para os 3 Workers

| Campo | Valor |
|---|---|
| **Onda** | 3 — Alertas + Health Checks |
| **Camada** | Workers |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 7 – Sem 8 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** os 3 Windows Services rodam continuamente (Tasks a cada 5s, FileExporter a cada 24h, Sync por unidade) e, se travarem, não há detecção. Instrumentar `SentrySdk.CaptureCheckIn(InProgress/Ok/Error)` por ciclo de cada worker para alertar quando um deles ficar **N minutos sem executar**.

**Evidência:** estudo item #8; `project.hasMonitors = False` (Sentry).

**Dependência:** depende da cobertura dos Workers (Etapa 10).

**Critério de pronto:** Cron Monitors dos 3 Workers ativos, com alerta de "não executou no prazo".

---

## Etapa 20 — Integração de alertas em canal (Slack/Teams) + ticket + CODEOWNERS

| Campo | Valor |
|---|---|
| **Onda** | 3 — Alertas + Health Checks |
| **Camada** | Automed (transversal) |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 8 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** plugar as regras de alerta num **canal (Slack/Teams)** e criar **ticket automático**; configurar **CODEOWNERS** para roteamento da issue ao dono. A única regra do org notifica por **e-mail genérico** — e o `automed` nem está nela. Definir Slack **ou** Teams como canal oficial.

**Evidência:** a regra existente usa `NotifyEmailAction` para `IssueOwners`; `automed` fora dela.

**Dependência:** depende de N1/N2/N3 (Etapa 16, gate) e das regras com filtro de ambiente (Etapa 17).

**Critério de pronto:** alertas chegando ao N1 por Slack/Teams + ticket automático; CODEOWNERS configurado.

---

# ONDA 4 — Performance + Logs Correlacionados (Semanas 8–10)

> Atacar a lentidão de banco que já aparece como timeout, ligar o trace entre API e Workers (que conversam por Refit) e **centralizar os logs dos Workers** (hoje presos no Windows Event Viewer). "Pronto" quando houver trace API↔Worker e salto erro↔log.

---

## Etapa 21 — Tratar timeouts de SQL + performance nos endpoints críticos

| Campo | Valor |
|---|---|
| **Onda** | 4 — Performance + Logs |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 8 – Sem 9 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** `SqlException: Execution Timeout Expired` em `Sql.FetchAll` (**AUTOMED-7 3 ev + AUTOMED-4 1 ev**) indica query lenta / falta de índice / contenção. Com `TracesSampleRate` ativo (estudo item #1, 0.1), instrumentar a latência dos endpoints críticos (`/eventos`, `/entidades`) com tag `organizacao_id` e atacar as queries que estouram timeout.

**Evidência:** AUTOMED-7/4 (Execution Timeout); estudo item #11 (performance nos endpoints críticos).

**Critério de pronto:** queries de timeout corrigidas; latência por endpoint/organização visível.

---

## Etapa 22 — Tracing API ↔ Workers (Refit)

| Campo | Valor |
|---|---|
| **Onda** | 4 — Performance + Logs |
| **Camada** | Automed (transversal) |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 9 – Sem 10 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** os Workers consomem a API via **Refit + JWT** (não acessam o banco direto). Propagar o `trace_id` da operação do worker para a chamada HTTP à API (`POST /eventos` etc.), para seguir um **ciclo de sync ponta a ponta**: coleta no XConnect/PI → POST na API → persistência. Hoje não dá para correlacionar a falha do worker com o request na API.

**Evidência:** doc (Workers via Refit+JWT).

**Dependência:** depende da cobertura dos Workers (Etapa 10).

**Critério de pronto:** trace contínuo do worker à API numa mesma operação de sync.

---

## Etapa 23 — Centralizar logs dos Workers e correlacionar com Sentry

| Campo | Valor |
|---|---|
| **Onda** | 4 — Performance + Logs |
| **Camada** | Workers |
| **Esforço** | **G (> 5 dias)** |
| **Semanas** | Sem 9 – Sem 10 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** os Workers logam no **Windows Event Viewer** (Application Log, source `Automind.Automed.Sync.PI [Ambiente] [Versão]`) — **sem agregação central** nem correlação com o erro no Sentry. Definir destino centralizado (ex.: **Application Insights / Seq / ELK**) e incluir `trace_id` para **saltar do erro no Sentry ao log estruturado** da mesma execução.

**Evidência:** doc (logs no Event Viewer, sem agregação). É um **gap vs AutoChecker**, que já tem Loki/Promtail.

**Critério de pronto:** logs dos Workers num destino central e pesquisável; salto erro↔log via `trace_id`.

---

# ONDA 5 — Métricas de Negócio + Dashboard (Semanas 10–12)

> Medir o **negócio**, não só a infraestrutura: produção sincronizada, fluxo ANP e saúde das tarefas, por organização e por fluxo. "Pronto" quando o dashboard por organização/fluxo estiver exibível.

---

## Etapa 24 — Definir métricas de negócio do Automed

| Campo | Valor |
|---|---|
| **Onda** | 5 — Métricas + Dashboard |
| **Camada** | Automed (transversal) |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 10 – Sem 11 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** definir as métricas:
- **produção sincronizada/dia** por unidade e por organização;
- **arquivos ANP** gerados / enviados / aceitos / aceito_parcial / rejeitados;
- **latência do ciclo de sync** (XConnect/PI/Scan);
- **tarefas executadas vs não executadas** (Tasks.Worker);
- **notificações de desvio** enviadas; **tempo até envio à ANP**.

**Racional:** base para **SLAs por organização** e visibilidade para liderança.

**Critério de pronto:** conjunto de métricas de negócio definido e mensurável.

---

## Etapa 25 — Dashboard por organização e por fluxo (Sync → Tasks → ANP)

| Campo | Valor |
|---|---|
| **Onda** | 5 — Métricas + Dashboard |
| **Camada** | Automed (transversal) |
| **Esforço** | **G (> 5 dias)** |
| **Semanas** | Sem 11 – Sem 12 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** dashboard por **organização** (tenant) e por **fluxo de negócio** (coleta/sync → fila de tarefas → geração/validação/envio ANP), **não** por módulo técnico. **Semáforo** de saúde do sync por unidade e do envio ANP por organização — exibível para liderança e suporte.

**Dependência:** consome as métricas da Etapa 24 e a instrumentação do pipeline (Etapa 13).

**Critério de pronto:** dashboard por organização/fluxo exibível, com semáforo de sync e de envio ANP.

---

# ONDA 6 — Endurecimento, Regulatório e Compliance (Semanas 12–14)

> Tratar o que dá impacto regulatório direto (ANP), os terceiros (XConnect/PI por organização), a rastreabilidade de desvios/importações e a segurança adjacente. "Pronto" quando rejeição/prazo ANP forem alertados e a conectividade por organização for monitorada.

---

## Etapa 26 — Rastreabilidade do fluxo ANP (Validar → Gerar → Enviar → Situação)

| Campo | Valor |
|---|---|
| **Onda** | 6 — Endurecimento + Regulatório |
| **Camada** | Tasks.Worker |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 12 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** o **motivo de existir** do produto. `AnpService` integra o **i-Engine da ANP** (SOAP/XML). Instrumentar o ciclo `ArquivoAnp` carregado → `ValidarArquivoAnp` → válido/inconsistente → `EnviarArquivo` → enviado/rejeitado → `AtualizarSituacaoArquivo` (aceito/aceito_parcial/rejeitado). Tratar com contexto: `Arquivo Inválido` (**AUTOMED-C**), `BTP já enviado` (**AUTOMED-X**), `BSWFiscal já cadastrado` (**AUTOMED-B**). **Alertar rejeição/prazo perdido como evento de NEGÓCIO** (impacto de multa/auditoria), mesmo com volume baixo.

**Evidência:** AUTOMED-C/X/B (Sentry); doc (erro regulatório tem impacto de multa mesmo com volume baixo); estudo item #7.

**Critério de pronto:** ciclo ANP rastreável por arquivo/organização; rejeição/prazo perdido vira alerta de negócio.

---

## Etapa 27 — Monitorar conectividade XConnect/PI por organização

| Campo | Valor |
|---|---|
| **Onda** | 6 — Endurecimento + Regulatório |
| **Camada** | Sync.Worker |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 12 – Sem 13 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** a sync depende de uma `ConnectionString` SQL Server **por organização** (`configuracao.XConnect.ConnectionString`) e do **PI AF Server**. Se a rede do cliente cair ou a senha mudar, o sync falha sem alerta. Capturar `SqlException` de conexão como evento com tags `sync.tipo`/`organizacao`/`unidade` e `sql.error_number` — **sem logar a connection string**.

**Evidência:** estudo item #6. Permite **diagnóstico remoto por organização** sem acesso ao ambiente do cliente.

**Critério de pronto:** falhas de conectividade XConnect/PI geram alerta identificando organização e unidade, sem expor credenciais.

---

## Etapa 28 — Rastrear notificações de desvio de medição + importação de arquivos ANP

| Campo | Valor |
|---|---|
| **Onda** | 6 — Endurecimento + Regulatório |
| **Camada** | Tasks.Worker |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 13 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** `NotificarDesviosMedicao` avisa quando medições desviam de limites regulatórios e `ImportarArquivoAnp` processa arquivos da ANP. Adicionar breadcrumbs/contexto (`organizacao`, tipo, arquivo) e capturar falhas — **evidência de que o sistema notificou/importou corretamente** em caso de questionamento regulatório.

**Evidência:** estudo itens #7 e #10.

**Critério de pronto:** histórico de notificações de desvio e de importações ANP rastreável no Sentry.

---

## Etapa 29 — Endurecimento de segurança adjacente (brute-force, CORS)

| Campo | Valor |
|---|---|
| **Onda** | 6 — Endurecimento + Regulatório |
| **Camada** | API |
| **Esforço** | M (2–5 dias) |
| **Semanas** | Sem 13 – Sem 14 |
| **Responsável** | A definir |
| **Status** | Não iniciado |

**O que fazer:** a API tem **rate limiting de 5 tentativas de login/min por IP**; tentativas bloqueadas são descartadas sem visibilidade (ataque distribuído passa despercebido) — capturar o `429` como **warning** com o IP. O volume de `UsuarioSendoUtilizado` (**AUTOMED-5, 49 ev**) no Login também merece análise. Revisar **CORS configurável por organização**. Priorizar com o time de segurança.

**Evidência:** estudo item #12 (rate limit no login); AUTOMED-5 49 ev (Sentry).

**Critério de pronto:** padrões de brute-force visíveis no Sentry; CORS revisado por organização.

---

# Anexos

## A. Distribuição de esforço

| Esforço | Itens | Quantidade |
|---|---|---|
| **P** (≤ 1 dia) | 5, 12 | 2 |
| **M** (2–5 dias) | 1, 2, 3, 4, 6, 7, 8, 9, 11, 14, 15, 16, 17, 18, 19, 20, 21, 22, 24, 26, 27, 28, 29 | 23 |
| **G** (> 5 dias) | 10, 13, 23, 25 | 4 |

## B. Correção de premissa vs estudo estático de abril

| Tema | Era (abril) | Realidade (junho) |
|---|---|---|
| Instalação | "Sentry não instalado em nenhum componente" | **API .NET já captura desde 14/04** (projeto `automed`) |
| Workers | totalmente silenciosos | erros do `Tasks.Core` **já aparecem**; Sync/FileExporter a confirmar |
| 3º Worker | `XConnect.Worker` | **`FileExporter.Worker`** (XConnect é sub-worker do Sync) |
| Ruído dominante | não previsto | **schema drift + migração por organização + ruído de host** (Sentry) |

## C. Dependências-chave entre etapas

| Etapa | Depende de | Motivo |
|---|---|---|
| 13 | 10 | instrumentar o sync exige o Sync.Worker já com Sentry |
| 17 | 1 | regras por ambiente exigem `environment` saneado |
| 19 | 10 | cron monitors exigem os Workers já com Sentry |
| 20 | 16, 17 | canal de alerta exige N1/N2/N3 + regras por ambiente |
| 22 | 10 | tracing API↔Worker exige Workers já com Sentry |
| 25 | 13, 24 | dashboard consome pipeline instrumentado + métricas definidas |
| Tudo (Ondas 1–6) | Onda 0 | **gate** — nada amplia antes do saneamento |

## D. Riscos e bloqueadores transversais

| Risco / Bloqueador | Dependência crítica |
|---|---|
| Schema drift código×banco (~247 ev) | Etapa 3 |
| Migração não chega a todos os schemas (~71 ev) | Etapa 4 |
| `environment` achatado (1 só env) | Etapa 1 |
| Workers e Frontend cegos | Etapas 10 e 11 |
| Domínio tratado como error (~70+ ev) | Etapa 6 |
| Automed fora de qualquer regra de alerta | Etapa 17 |
| Risco regulatório ANP invisível | Etapa 26 |
| `ConnectionString` do XConnect (dado sensível) | Etapas 7/13/27 |
| Responsáveis "A definir" em todas as 29 linhas | atribuição de equipe |

## E. Referências (arquivos-fonte)

| Fonte | Caminho |
|---|---|
| Cronograma (HTML) | `Cronograma Observabilidade/AutoMed/Cronograma_Observabilidade_Automed_2026-06-08.html` |
| Cronograma (XLSX/PDF) | `Cronograma Observabilidade/AutoMed/Cronograma_Observabilidade_Automed_2026-06-08.{xlsx,pdf}` |
| Contexto de implantação | `Cronograma Observabilidade/AutoMed/Contexto_Observabilidade_Automed_2026-06-08.md` |
| Documentação de produto | `.claude/skills/produtos-automind/references/automed.md` · `Produtos/Automed-documentacao.pdf` |
| Estudo estático | `Estudo de melhoria de observabilidade/Oportunidades de Melhoria de Observabilidade - Automed.md` |
| Snapshot Sentry | `gerador de relatorios/_data_2026-06-01__2026-06-07/` (projeto `automed`) |

---

> **Notas finais:**
> - **Semanas relativas:** a âncora de calendário (qual é a Semana 1) ainda não está definida nas fontes.
> - **Responsáveis:** "A definir" em todas as 29 etapas — atribuir donos é um dos primeiros passos da execução.
> - **Janela Sentry:** contagens de 7 dias (01–07/06/2026); confirmar tendência de 30 dias no próximo snapshot.
> - **Nenhum item deve ser implementado sem revisão e aprovação do time de arquitetura.**
> - Documento gerado em 08/06/2026 a partir do cruzamento das fontes do Automed (doc + Sentry + estudo estático).
