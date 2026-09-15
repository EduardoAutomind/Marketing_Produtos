# Detalhamento das Ondas 0 a 4 — Como resolver cada etapa (Cronograma de Observabilidade · AutoChecker)

> **Estudo fundamentado em 3 fontes (sem informação inventada):** código real, documentação e Sentry ao vivo.
> Onde as 3 fontes não bastam, está marcado **Parcial** ou **Não sei**.

| | |
|---|---|
| **Data da análise** | 2026-06-12 (Ondas 0–3) · **2026-06-17 (Onda 4, ao vivo)** |
| **Escopo** | Onda 0 (1–8) · Onda 1 (9–13) · Onda 2 (14–16) · Onda 3 (17–21) · **Onda 4 (22–24)** |
| **Produto** | AutoChecker — SaaS multi-tenant de validação documental (Django 4.2 + DRF · Celery 5.3 · Next.js 14 · OCR/AIAgent/APP/Custos) |
| **Ferramenta** | Sentry — org `automind-qd` · projetos `autochecker-backend` / `-worker` / `-frontend` |
| **Cronograma-base** | `Cronograma_Observabilidade_AutoChecker_2026-06-03.xlsx` (REV pós-auditoria 10/06) |

---

## Fontes consultadas

| Fonte | Localização | Uso nesta análise |
|---|---|---|
| **Código real** | `C:\Projetos\automind-obs\Produtos\Autochecker\` → monorepo `AutoChecker\` (`backend\`, `worker\`, `shared\`, `frontend\`) + serviços `AutoChecker_Frontend\`, `AutoChecker_OCR\`, `AutoChecker_AIAgent\`, `AutoChecker_APP\`, `AutoChecker_Custos\`, `Scrapping\` | Citações `arquivo:linha` verificadas em 12/06 |
| **Documentação** | `Estudo de melhoria de observabilidade\` → `AutoChecker-documentacao.md` (§ citadas), `Oportunidades de Melhoria…AutoChecker.md` (ESTÁTICO 14/04, 11 itens), `Roadmap_Observabilidade_AutoChecker.md`, `Questionario_Sentry_Respostas_Dev_2026-05.md` | Corroboração técnica |
| **Sentry (MCP)** | org `automind-qd` (regionUrl `https://us.sentry.io`) | Validação ao vivo (12/06) |
| **Análises por etapa já existentes** | `Etapa2_Release_SetCommits_Pipelines_AutoChecker.md`, `Etapa3_PeriodicTask_Orfa_Beat_AutoChecker.md` | Itens 2 e 3 (incorporados aqui de forma resumida) |

---

## Ressalvas globais (valem para todos os itens)

1. **Doc de auditoria citado no xlsx não existe como arquivo.** O cronograma atribui as revisões "REV 10/06" a `Auditoria_Cronograma_vs_Codigo_AutoChecker_2026-06-10`, **que não está em nenhum dos repositórios** (só existe a `Auditoria_Observabilidade_AutoChecker_2026-06-03`). As notas REV estão dentro do próprio xlsx e foram revalidadas direto no código nesta análise.
2. **Dois frontends coexistem** com config Sentry idêntica: `AutoChecker_Frontend\` (repo dedicado) e `AutoChecker\frontend\` (monorepo). Diferem em ~7 linhas do `next.config.js` (bloco `compiler.removeConsole`). **Qual está em produção precisa ser confirmado com o time** (afeta itens 1, 2, 7, 11). Toda correção de frontend deve ir no que faz deploy.
3. **Semanas relativas** (Sem 1–16), sem datas-âncora; **responsáveis "A definir"** em todos os itens.
4. **Snapshot × ao vivo:** os percentuais de `environment` do xlsx vêm do snapshot 04/05→03/06 sobre *todos os eventos*; a checagem ao vivo (12/06) é *errors/30d* — janela/métrica diferente, não contradição.

### Legenda

- **Status (cronograma):** o que o xlsx declara.
- **Veredito (situação real):** Cumprida / Parcial / **Não cumprida**, com base no código.
- **Confiança:** **Sei** (3 fontes concordam) · **Parcial** (parte não verificável/divergente) · **Não sei**.
- **Esforço:** P (≤1 dia) · M (2–5 dias) · G (>5 dias).

---

# ONDA 0 — Saneamento da Base
**GATE: nada de ampliação antes disto · Sem 1–2**

---

## Item 1 — Padronizar tag `environment` nos 3 SDKs + isolar DEV/PRD
`Camada: Frontend/Worker · Esforço: M · Status: Concluído · Veredito: Parcial · Confiança: Parcial`

### O que a etapa exige
Garantir `environment ∈ {production, staging, development}` em backend, worker e frontend; isolar o ambiente dev local do projeto produtivo. **KPI:** ≥99% dos eventos com environment correto em 7 dias.

### O que cada fonte mostrou
- **Código (CONFIRMADO):** os 3 SDKs leem env var com fallback `"development"`:
  - Backend → `backend/config/settings/base.py:730` → `environment=os.environ.get("SENTRY_ENVIRONMENT", "development")`
  - Worker → `worker/config/celery.py:24` → idem
  - Frontend → `instrumentation-client.ts:9`, `sentry.server.config.ts:9`, `sentry.edge.config.ts:10` → `process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development"`
  - Isolamento por **guard de DSN**: backend/worker `shared/observability/sentry.py:16-18` (`if not dsn: return`); frontend `enabled: !!NEXT_PUBLIC_SENTRY_DSN`. Não há DSN diferente "hard-coded" por ambiente — depende da env var bem setada no deploy.
- **Documentação:** §7 confirma a causa do problema no frontend ("fallback `development` → DEV poluindo prod") e os percentuais do snapshot (backend 96%, frontend 15%, worker 65%).
- **Sentry ao vivo (12/06, dataset errors / 30d):**
  | Projeto | production | staging | development |
  |---|---|---|---|
  | backend | 11.458 | 54 | — |
  | worker | 725 | 28 | — |
  | frontend | 27 | 8 | — |

  Ou seja, ao vivo (só erros, 30d) os 3 projetos aparecem majoritariamente em `production` e **sem** `development` no dataset de errors — diferente do snapshot.

### Veredito
**Parcial.** O **código já padroniza** environment com fallback — o lado de código da etapa está feito (condiz com "Concluído"). Mas o **isolamento real depende do deploy** setar `*_SENTRY_ENVIRONMENT` corretamente, e o fallback `development` continua sendo a porta de poluição se a env var faltar. O ganho só "fecha" quando o KPI ≥99% for medido na janela produtiva.

### Plano de resolução
1. Garantir nos 4 pipelines Azure que `SENTRY_ENVIRONMENT` (backend/worker) e `NEXT_PUBLIC_SENTRY_ENVIRONMENT` (frontend) sejam **sempre** setados — nunca cair no fallback. Considerar **falhar o build** se a var estiver vazia em prod.
2. Confirmar **qual frontend** faz deploy (ressalva global #2) e aplicar lá.
3. Bloquear máquina dev de enviar ao projeto produtivo: DSN de dev separado (ou `enabled:false`/sem DSN em dev).
4. Medir o KPI ≥99% sobre **todos os eventos** na janela de 7 dias, por projeto.

### Ressalva
O número "15% production" do xlsx **não foi reproduzido** ao vivo via MCP no dataset de **errors/30d** — para reproduzir seria preciso a distribuição de **todos os eventos** (transactions/replay) na janela do snapshot, que o dataset de errors não entrega diretamente. Logo, o "como está hoje" do frontend fica **Parcial**.

---

## Item 2 — Padronizar release `<comp>@<hash>` + set-commits + isolar pipelines Azure
`Camada: AutoChecker · Esforço: M · Status: Em andamento · Veredito: Não cumprida · Confiança: Sei`
*(Detalhe longo em `Etapa2_Release_SetCommits_Pipelines_AutoChecker.md`.)*

### O que a etapa exige
Quatro entregas: (1) release consistente `<componente>@<hash>` nos 3 serviços; (2) `set-commits --auto` (suspect commits); (3) isolar as 4 pipelines Azure (backend, frontend, worker, tests) — dev não publica no projeto produtivo; (4) corrigir o org/project default do `withSentryConfig` no frontend.

### O que cada fonte mostrou
- **Código (CONFIRMADO):** os **dois** `next.config.js` (`AutoChecker_Frontend\next.config.js` e `AutoChecker\frontend\next.config.js`) usam `withSentryConfig` com defaults **errados**:
  - `org: process.env.SENTRY_ORG || "automind-teste"`
  - `project: process.env.SENTRY_PROJECT || "javascript-nextjs"`
  - **sem** chave `release`; **sem** `setCommits`.
  - Única diferença real entre os dois arquivos: bloco `compiler.removeConsole` (presente só no `AutoChecker_Frontend`, linhas 8-13). O resto é cópia.
  - Correto (pelo próprio cronograma): org `automind-qd`, project `autochecker-frontend`.
  - Isolamento de pipelines → vive no Azure DevOps; **não** atestável por estes arquivos.
- **Documentação:** §4 confirma os defaults de teste (`automind-teste`/`javascript-nextjs`). `CLAUDE.md` indica `AutoChecker/frontend/` como diretório oficial → `AutoChecker_Frontend/` é provavelmente cópia antiga.
- **Sentry:** sem `SENTRY_ORG`/`SENTRY_PROJECT` no CI, source maps e releases vão para o **projeto errado** — e suspect commits / correlação picos×deploys ficam bloqueados.

### 🔎 Discrepância — dois `next.config.js` divergentes
Manter dois configs divergentes permite buildar a partir do diretório errado e mandar telemetria para o lugar errado. Decidir o canônico é pré-requisito (cruza a ressalva global dos "dois frontends").

### Veredito
**Não cumprida.** Apesar do status "Em andamento" no cronograma, o código mostra a etapa **intocada**: org/project ainda de teste, sem release, sem set-commits. (A parte de isolamento de pipelines não é verificável pelos arquivos de frontend, mas o status global é não iniciado.)

### Plano de resolução
1. **Passo 0 — diretório canônico:** confirmar que `AutoChecker/frontend/` é o de produção e arquivar/deletar o duplicado (**precisa OK explícito — apaga pasta**).
2. **Passo 1 — `withSentryConfig`:** trocar para `org:"automind-qd"`, `project:"autochecker-frontend"`, adicionar `release.name=$SENTRY_RELEASE` e `setCommits:{auto:true}`; **preservar** `hideSourceMaps:true` e `widenClientFileUpload:true`.
3. **Passo 2 — pipeline frontend:** definir `SENTRY_RELEASE = autochecker-frontend@<git-hash>`; garantir `ORG/PROJECT/AUTH_TOKEN` vindos do CI (não do default). Isso já isola o frontend: **só o CI tem o token.**
4. **Passo 3 — backend/worker:** replicar release `<comp>@<hash>` (Python SDK) — conecta com o item 5.
5. **Passo 4 — Azure:** isolar as 4 pipelines (bloquear envio de máquinas dev; separar ambientes).

### Ressalva
Confirmar 100% os valores `automind-qd`/`autochecker-frontend` antes de aplicar (errar = telemetria some). Isolamento de pipelines não é atestável por estes arquivos.

---

## Item 3 — Limpar PeriodicTask órfã do Beat (`KeyError process_scheduled_notifications`)
`Camada: Backend/Worker · Esforço: P · Status: Pendente · Veredito: Não cumprida · Confiança: Sei`
*(Detalhe longo em `Etapa3_PeriodicTask_Orfa_Beat_AutoChecker.md`.)*

### O que a etapa exige
Remover/migrar a entrada órfã persistida e alinhar o schedule persistido com o do código. Era o **maior ruído do produto**: ~1.640 ev (clusters BACKEND-1H / WORKER-1F).

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Task `process_scheduled_notifications` **comentada** em `worker/apps/notifications/tasks/notification_tasks.py:49-67` (e `cleanup_old_notification_logs` em 70-87) → fora de qualquer `beat_schedule`.
  - `worker/config/celery.py:69` define o `beat_schedule` no código e **não** contém a task.
  - `backend/config/celery.py:23-25` deliberadamente **não** define `beat_schedule`.
  - **Bug colateral:** o worker redefine `retry_failed_notifications` localmente (`worker/apps/notifications/tasks/notification_tasks.py:90`) chamando `process_notification_task.delay(notification.id)` com **1 argumento** (linha ~110), enquanto a assinatura exige `(notification_log_id, tenant_schema_name, tenant_id)` → `TypeError` em runtime. A versão correta está no `shared`.
- **Documentação:** §7 — `KeyError …process_scheduled_notifications` ~1.640 ev: task comentada → entrada órfã ainda agenda → KeyError no dispatch.
- **Sentry:** snapshot — clusters BACKEND-1H / WORKER-1F (~1.640 ev).

### 🔎 Discrepância — a órfã provavelmente NÃO está no DB
O xlsx assume a órfã no DB do `django-celery-beat` (`PeriodicTask`). Mas o Beat real roda com **PersistentScheduler** (arquivo shelve): `celery -A config beat --schedule=/tmp/celerybeat-schedule` (docker-compose.prod.yml:135 / dev.yml:120). **Não há** flag `--scheduler django_celery_beat.schedulers:DatabaseScheduler` nem setting `CELERY_BEAT_SCHEDULER`. `django_celery_beat` está em `INSTALLED_APPS` (`worker/config/settings/base.py:49`) mas **não é usado** como scheduler. O volume `/tmp:/tmp` torna o arquivo persistente entre restarts. → A órfã muito provavelmente vive no **arquivo `/tmp/celerybeat-schedule`**, não no DB. **Verificar os dois.**

### Veredito
**Não cumprida** (no máximo parcial — lado código). Comentar a task foi o que *criou* a órfã; o código já está limpo, falta o **expurgo runtime/ops**, que nenhum arquivo-fonte faz (nem poderia).

### Plano de resolução
1. **Diagnosticar onde a órfã vive:** inspecionar `/tmp/celerybeat-schedule*` (shelve) no container do beat **e** `PeriodicTask.objects.filter(task__icontains='process_scheduled_notifications')` no DB.
2. **Expurgar:** se for o arquivo (mais provável), parar o beat, `rm -f /tmp/celerybeat-schedule*` e subir (recria do `beat_schedule` do código); se houver linha no DB, **data migration idempotente** (`PeriodicTask…filter(task__endswith='process_scheduled_notifications').delete()`).
3. **Travar a fonte de verdade:** não misturar file scheduler com `DatabaseScheduler` (a mistura gera órfãs).
4. **Corrigir o bug colateral:** remover a `retry_failed_notifications` local/bugada do worker e reexportar a do `shared` (como o backend faz).
5. **Validar:** sem mais `KeyError: process_scheduled_notifications` no dispatch; queda dos clusters BACKEND-1H / WORKER-1F (~1.640 ev → ~0). Adicionar teste de guarda: cada task do `beat_schedule` registrada no app Celery.

### Ressalva
O expurgo é **runtime** (não versiona em código). Apagar arquivo de ambiente ou rodar migration de delete → **confirmar antes**. Confirmar se algum host já rodou com `DatabaseScheduler` (decide se a migration é necessária).

---

## Item 4 — Corrigir migrações faltando em schemas de tenant (`relation does not exist`)
`Camada: Worker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Trocar o `migrate` simples do deploy por `migrate_schemas` e adicionar **gate** que falha o deploy se houver migração pendente em **qualquer** schema. O gap real é o **drift de tenants PRÉ-EXISTENTES**.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Deploy roda `migrate` simples: `backend/scripts/deploy.sh:97` (`python manage.py migrate --settings=config.settings.production`) e `backend.azure-pipelines.yml:148` (`migrate --plan`) / `:157` (`migrate`).
  - `migrate_schemas` só aparece em: `backend/apps/tenants/signals.py:12` **e `worker/apps/tenants/signals.py:12`** (migra tenant **novo** na criação, dentro de `if created:`) e `backend/scripts/reset_db_django.py:126` (`migrate_schemas --shared`, fora do deploy regular).
  - **Não há** management command de "check drift" nem gate de migração pendente no deploy → tenants pré-existentes ficam órfãos de migração.
- **Documentação:** §2.2 confirma textualmente ("deploy roda `migrate`/`migrate --plan` … nunca `migrate_schemas` … não há gate de migração por schema").
- **Sentry ao vivo (12/06):** `WORKER-1G` *relation "notifications_notificationlog" does not exist* **544 ev** (culprit `shared.tasks.notification_tasks.retry_failed_notifications`); `WORKER-C` *relation "notifications_reportpreference" does not exist* **153 ev**. Snapshot: ~57 issues / ~1.267 ev.

### Veredito
**Não cumprida** (confere com "Não iniciado"). Premissa correta e confirmada nas 3 fontes; correção REV 10/06 (`migrate_schemas` também em `signals.py`) validada — e existe nas **duas** cópias (backend e worker).

### Plano de resolução
1. No deploy (`deploy.sh:97` + `backend.azure-pipelines.yml:148/157`) trocar `migrate` por **`migrate_schemas`**. Avaliar `--executor multiprocessing` pelo tempo de deploy.
2. **Gate de drift:** passo no pipeline com `migrate_schemas --check` (ou `migrate --check` por schema) que **falha** se houver migração não aplicada em qualquer schema.
3. **Backfill** único nos tenants pré-existentes em drift (rodar `migrate_schemas` controlado antes de ligar o gate).
4. Excluir o schema `public` dos alertas que medem esse erro (cruza item 8).

### Ressalva
`migrate_schemas` em produção multi-tenant é operação pesada/long-running — planejar janela e idempotência.

---

## Item 5 — Consolidar init do Sentry no helper `init_sentry` (+ CeleryIntegration no backend)
`Camada: Backend/Worker · Esforço: P · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Backend e worker fazem `sentry_sdk.init` **direto** e divergem; o helper `shared/observability/sentry.py` existe mas ninguém chama. Migrar ambos para `init_sentry(service)`. **Atenção (REV 10/06):** o helper só dá `CeleryIntegration` quando `service=='worker'` — **trocar só a chamada não dá CeleryIntegration ao backend**; é preciso alterar o helper.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Backend init inline `base.py:728-736`: integrations `[DjangoIntegration(), RedisIntegration()]` (**sem Celery**), `before_send=_sentry_before_send` (filtra `/health/` e ruído transiente de Redis via `_is_redis_transient_event`, `:713-723`).
  - Worker init inline `worker/config/celery.py:22-32`: `[DjangoIntegration(), CeleryIntegration(), RedisIntegration()]`, `before_send` = lambda que **só** filtra `/health/` (**sem** scrubbing de breadcrumb).
  - Helper `shared/observability/sentry.py:9-38`: adiciona `CeleryIntegration` **apenas** se `service_name == "worker"` (`:25-26`); `before_send_filter` (`:41-51`) faz **scrubbing de query nos breadcrumbs** (`:46-49`) — proteção que o init inline do worker **não** tem.
  - `init_sentry(` **nunca é chamado** em produção — só em `shared/observability/tests/test_sentry.py`. Confirmado por busca global.
- **Documentação:** §6 ("helper… não é chamado por ninguém → config duplicada e drift") e confirma os dois inits + ausência de Celery no backend.
- **Sentry:** não aplicável diretamente (questão de configuração de SDK).

### Veredito
**Não cumprida** (confere com "Não iniciado"). A correção REV 10/06 do xlsx está **certa**: o helper hoje **não daria** CeleryIntegration ao backend.

### Plano de resolução
1. **Alterar o helper** `init_sentry` para dar CeleryIntegration ao backend também (o backend Django enfileira tasks → eventos de Celery são úteis), ou parametrizar as integrations explicitamente por serviço.
2. Migrar `base.py:728` e `celery.py:22` para `init_sentry("backend")` / `init_sentry("worker")`, **preservando** o que hoje só existe inline: filtro de **Redis transiente** (backend); o worker ganha o **scrubbing de breadcrumb** de brinde ao usar o helper.
3. Fixar `send_default_pii=False` explicitamente (cruza item 7). Teste de guarda afirmando o conjunto de integrations esperado por serviço.

### Ressalva
Não perder o `_is_redis_transient_event` do backend ao consolidar — hoje ele só existe no init inline.

---

## Item 6 — beforeSend / Inbound Filters: scanner, ruído de auth e filtro de health morto
`Camada: Backend · Esforço: M · Status: Em andamento (parcial) · Veredito: Parcialmente cumprida · Confiança: Sei`

### O que a etapa exige
Filtrar `DisallowedHost` (scanner de IP) via ALLOWED_HOSTS/Inbound Filter; **não** dropar auth em bloco (são incidentes reais — reclassificar por endpoint/causa); e **corrigir o caminho de health nos dois filtros mortos** (`before_send` em `base.py:716` e middleware `api_logging.py:18`).

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - `before_send` `base.py:713-723` casa `event…url.endswith("/health/")`.
  - Middleware `api_logging.py:18` → `EXCLUDED_PATHS = {"/api/health/", "/health/"}`.
  - **Endpoint real = `/api/core/healthcheck/`**: `apps/core/urls.py:12` define `healthcheck/`, montado em `api/core/` por `config/urls_public.py:45` e `config/urls_tenant.py:76`. View trivial `apps/core/views.py:21` → `Response({"status": "ok"})` (**não** checa DB/Redis/broker; **não** usa `django-health-check`). Doc §3 confirma e diz que **não existe** rota `/health/`.
  - **Conclusão:** os dois filtros casam `/health/` (inexistente) → **filtro morto**; e nenhum exclui `/healthcheck/`.
  - `DisallowedHost`: **sem tratamento dedicado para Sentry**; `ALLOWED_HOSTS` em `production.py:14-20` (e wildcard `*` em `development.py`). Não há Inbound Filter/`before_send` para `DisallowedHost`.
  - Tags de tenant: `api_logging.py:25-33` chama `set_tenant_context` (`tenant_id`/`schema_name`) — relevante ao item 9.
- **Documentação:** §3 e §7 confirmam (healthcheck real; `DisallowedHost` = scanner/ruído 127 ev; auth ~275 ev como falhas "esperadas" logadas como error).
- **Sentry:** snapshot — `DisallowedHost` (BACKEND-1A) 127 ev; auth ~275 ev. (Não re-medido ao vivo nesta rodada.)

### Veredito
**Parcialmente cumprida** (reavaliado ao vivo em 2026-06-15). A **fundação avançou**, mas **nenhum dos 3 entregáveis nomeados** está concluído:

| Sub-item | Status | Evidência (conferida 2026-06-15) |
|---|---|---|
| Fundação: `before_send` ativo + filtro de Redis transiente | 🟢 backend / 🟠 worker | `base.py:713` ativo; Redis transiente filtrado em `base.py:720` (`_is_redis_transient_event`). Worker (`worker/config/celery.py`) tem só `/health/`, **sem** filtro de Redis. |
| (1) Corrigir filtro de health morto | 🔴 ainda morto | `base.py:716` segue casando `.endswith("/health/")`; endpoint real é `/api/core/healthcheck/` (`apps/core/urls.py:12`, confirmado). O filtro "opera" mas **nunca casa** o health. |
| (2) `DisallowedHost` (scanner) | 🔴 não feito | Ainda fluindo ao vivo: `BACKEND-1A` (128 ev) + `BACKEND-17` (41 ev). Sem Inbound Filter dedicado. |
| (3) Reclassificar ruído de auth por endpoint | 🔴 não feito (**piorou**) | `token.py:94` ainda loga `ERROR` para anônimo esperado; `JWT_SKIP_PATHS` segue com 4 rotas. Ruído **expandiu** para rotas novas (legal/documents, reset-password, mobile/*), lastSeen ~37 min. |

> ⚠️ A frase do relatório semanal "o filtro de ruído de infraestrutura entrou em operação" refere-se à **ativação do `before_send`** (que de fato descarta blips de Redis) — não à filtragem de health, que continua apontando para o caminho errado.

### Plano de resolução
1. **Corrigir os filtros de health:** trocar `"/health/"` por `"/api/core/healthcheck/"` no `before_send` (`base.py:716`) e em `EXCLUDED_PATHS` (`api_logging.py:18`). Cruza com item 20 (tornar o healthcheck um readiness real).
2. **`DisallowedHost`:** filtrar via **Inbound Filter** no painel Sentry (mais simples que código) e/ou ajustar `ALLOWED_HOSTS`. Remover o wildcard `*` de `development.py` se vaza para prod.
3. **Auth: NÃO dropar em bloco.** Reclassificar por endpoint/causa (a análise viva de 09/06 mostra incidentes reais — Ultracargo em `/api/token/`, trial JWT em `/api/trial/public-config/`, fluxo de convite, forgot-password). Dropar só o que for comprovadamente scanner/ruído.

### Ressalva
A reclassificação de auth depende de análise por endpoint (não é regra única) — é trabalho de triagem, não só um filtro.

---

## Item 7 — Scrubbing de PII/LGPD no Frontend + Data Scrubber server-side
`Camada: Frontend · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Backend já tem `send_default_pii=False`. No frontend: pôr `sendDefaultPii:false`, masking/seletores de bloqueio no replay, e regras de Advanced Data Scrubbing na UI.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - `sendDefaultPii: true` em `instrumentation-client.ts:21`, `sentry.server.config.ts:16`, `sentry.edge.config.ts:17`.
  - `Sentry.setUser({ id, email })` em `modules/auth/hooks/useAuth.tsx:175` (login) e `:388` (selectTenant); `setUser(null)` no logout `:224`.
  - Session Replay `replaysSessionSampleRate: 0.1` / `replaysOnErrorSampleRate: 1.0` (`instrumentation-client.ts:18-19`), **sem** `maskAllText`/`blockAllMedia`/seletores — usa defaults do SDK.
  - Backend **`send_default_pii` não setado → default `False`** (ok) — `base.py:728-736` não menciona PII.
  - Custos `AutoChecker_Custos/src/instrument.ts:12` → `sendDefaultPii: true`.
- **Documentação:** §8 confirma tudo (inclui `.env.example` expondo `NEXT_PUBLIC_JWT_SECRET`; CPF/CNPJ em texto puro no DB).
- **Sentry:** não há o que medir por API; é configuração de SDK + regras de scrubbing no painel.

### Veredito
**Não cumprida** (confere). Premissa confirmada integralmente.

### Plano de resolução
1. Frontend: `sendDefaultPii:false` nos 3 configs; **masking do replay** (`maskAllText:true`, `blockAllMedia:true`, e seletores específicos nas telas de CNH/ASO/CPF). Confirmar qual frontend é o produtivo e aplicar nos dois se ambos forem deployados.
2. Reavaliar `Sentry.setUser` para enviar só `id` (sem `email`) — ou anonimizar.
3. **Advanced Data Scrubbing** (server-side, painel Sentry) como rede de segurança: regras para CPF/CNPJ/e-mail.
4. Corrigir `sendDefaultPii:true` do Custos.
5. (Compliance, fora do escopo de obs.) avaliar criptografia de CPF/CNPJ em repouso — cruza item 31.

### Ressalva
O `default False` do backend é por convenção do `sentry-sdk` (não há linha explícita) — correto, mas frágil; vale fixar `send_default_pii=False` explicitamente ao consolidar o init (item 5).

---

## Item 8 — Triagem ZERO do backlog (152 issues)
`Camada: AutoChecker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei (total: Parcial)`

### O que a etapa exige
Classificar todas as issues (Resolved / Ignored com prazo / In Progress), documentar critério, excluir o schema público dos alertas. Hoje **0 issues resolvidas em 30 dias**.

### O que cada fonte mostrou
- **Código:** nada a auditar — regras/alertas e status de issue **vivem só no painel Sentry** (busca por `alert`/`rule` no repo só achou componentes de UI).
- **Documentação:** §7 — "3 projetos · 152 issues · 0 resolvidas. Worker 94, backend 56, frontend 2."
- **Sentry ao vivo (12/06):**
  - `is:resolved` na org retorna **8 issues — todas do AutoLoad V4** (`AUTOLOADV4-EDGEGATEWAY-*`). **Nenhuma do AutoChecker.** → a afirmação "0 resolvidas no AutoChecker" **continua verdadeira hoje**.
  - Backlog do worker segue cheio e ativo (top por frequência): `WORKER-9 Task failed` **689 ev** (visto há ~29 min — subindo, bate com a sessão de hoje no FollowUp), `WORKER-1G relation…notificationlog` 544, `WORKER-5 site check` 314, `WORKER-K/N relatório/preferência` 242/241, `WORKER-2/1 Firebase/FCM` 171/169, `WORKER-C relation…reportpreference` 153, `WORKER-1R/1Q webhook 404` 135/135.

### Veredito
**Não cumprida** (confere). A triagem **não começou**: 0 resolvidas no AutoChecker até hoje.

### Plano de resolução
1. Definir **critério escrito** de triagem (quando Resolve / Ignore-com-prazo / In Progress) e dono por projeto.
2. Passar issue a issue (começar pelos top ofensores, que cruzam com itens 3/4/15/22/27/28): resolver as já corrigidas, **Ignore com prazo** o ruído (UNAVAILABLE, auth esperada), atribuir o resto.
3. **Excluir o schema `public`** dos alertas/queries (cruza itens 4 e 18).
4. Meta: backlog com dono e tendência de "resolved/30d" > 0.

### Ressalva
O total "152 issues" é do snapshot 04/05→03/06; o número exato de issues abertas **hoje** não foi recontado por API (o MCP lista issues, não devolve um total agregado simples). O que **foi** confirmado ao vivo é o fato crítico: **0 resolvidas no AutoChecker**.

---

### Resumo — Onda 0

| # | Etapa | Status cronograma | Veredito (situação real) | Confiança |
|---|---|---|---|---|
| 1 | environment nos 3 SDKs + isolar DEV/PRD | Concluído | **Parcial** — código pronto; isolamento depende do deploy/KPI | Parcial |
| 2 | Release `<comp>@<hash>` + set-commits + pipelines | Em andamento | **Não cumprida** — org/project default errado; sem release/set-commits | Sei |
| 3 | PeriodicTask órfã do Beat | Pendente | **Não cumprida** — código limpo; falta expurgo runtime (órfã provável em `/tmp/celerybeat-schedule`) | Sei |
| 4 | migrate_schemas + gate de drift | Não iniciado | **Não cumprida** — confirmada (ao vivo WORKER-1G 544 ev) | Sei |
| 5 | Consolidar init no `init_sentry` | Não iniciado | **Não cumprida** — helper nunca chamado; precisa alterar o helper | Sei |
| 6 | beforeSend / filtros / health morto | Em andamento (parcial) | **Parcial** (reav. 15/06) — `before_send` ativo (filtra Redis); health ainda casa `/health/` (real `/api/core/healthcheck/`), `DisallowedHost` e auth não feitos (auth piorou) | Sei |
| 7 | PII/LGPD no Frontend | Não iniciado | **Não cumprida** — `sendDefaultPii:true`×3 + setUser(email) + replay sem mask | Sei |
| 8 | Triagem ZERO do backlog | Não iniciado | **Não cumprida** — 0 resolvidas no AutoChecker (confirmado ao vivo) | Sei (total: Parcial) |

---

# ONDA 1 — Fundação dos SDKs
**Django + Celery + Next.js · Sem 3–4**

---

## Item 9 — Enriquecer contexto/tags no Backend (Django 4.2 + DRF)
`Camada: Backend · Esforço: M · Status: Não iniciado · Veredito: Parcial · Confiança: Sei`

### O que a etapa exige
Sobre o init consolidado (item 5): garantir tags globais coerentes (`tenant_id`, `schema_name` já existem no middleware) e **captura no ExceptionMiddleware sem duplicar eventos**.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - ExceptionMiddleware = `ApiRequestLoggingMiddleware.process_exception` (`api_logging.py:35-40`): `sentry_sdk.capture_exception(exception)` na linha **40** — único ponto explícito de captura no backend.
  - Tags via `set_tenant_context` (`api_logging.py:25-33`; definição `shared/observability/sentry.py:54-57` → `set_tag("tenant_id"…)`, `set_tag("schema_name"…)`).
  - Masking de chaves sensíveis: `SENSITIVE_KEYS = re.compile(r"password|token|secret|cpf|cnpj", IGNORECASE)` (`api_logging.py:8-9`), aplicado em `_sanitize_payload` (`:107-117`). Também em `audit.py:6`.
- **Documentação:** §3/§6 — `api_logging` é o único ponto com `capture_exception`; tags por request.
- **Sentry:** não aplicável diretamente.

### 🔎 Achado novo — risco de duplicação CONFIRMADO
`DjangoIntegration` já captura exceções automaticamente **e** o middleware chama `capture_exception` **sem re-raise** (loga e segue o pipeline). → o mesmo erro pode ir ao Sentry **2×**. É exatamente o "sem duplicar eventos" que o item 9 pede — o risco é real.

### Veredito
**Parcial** — as tags já existem (parte feita), mas há duplicação a resolver, e a etapa depende do init consolidado (item 5).

### Plano de resolução
1. **Deduplicar:** escolher **um** caminho — deixar o `DjangoIntegration` capturar e remover o `capture_exception` do middleware, **ou** manter só o middleware e desligar a captura automática dessas exceções.
2. Padronizar DSN/environment/release no init consolidado (depende do item 5).
3. Teste: uma exceção de view gera **1** evento, não 2.

---

## Item 10 — Enriquecer contexto/tags no Worker (Celery 5.3)
`Camada: Worker · Esforço: M · Status: Não iniciado · Veredito: Parcial · Confiança: Sei`

### O que a etapa exige
Tags globais por task: `task_name`, `queue`, `tenant_id`, `document_id`; reclassificar retries esperados (backoff em 429/5xx) para não inflarem como erro.

### O que cada fonte mostrou
- **Código:**
  - `task_prerun` (`worker/config/celery_logging.py:72-97`) já seta `task_name` (`sender.name`), `queue` (`_get_queue_from_delivery_info`), `tenant_id`/`schema_name` (via `set_tenant_context`, linha 83) e `retries`. **Falta `document_id`** — não é extraído de args/kwargs (cada task recebe `document_id`, ex. `entry.py:12`).
  - **11 filas** roteadas em `worker/config/settings/celery_settings.py:68-105` (`validation_entry`, `ocr_heavy`, `ai_processing`, `data_processing`, `auth_selenium`, `admin_tasks`, `monitoring`, `notifications`, `notifications_retry`, `reports`, `integrations`).
  - **2 pools** em `docker-compose.prod.yml`: **heavy** (`ocr_heavy, ai_processing, auth_selenium`, autoscale 2,1) e **light** (demais filas, autoscale 4,1).
  - **Retries:** `classification.py:295-324` trata `openai.RateLimitError` (429) corretamente — `logger.warning` + `self.retry()` com backoff, marca `ai_quota_exhausted`, **sem** `capture_exception`. `ocr.py` (404/419/498) e `entry.py:54` fazem retry **genérico** sem discriminar 429/5xx. Handler `task_retry` (`celery_logging.py:162-180`) loga `warning`.
- **Documentação:** §2.3 — 11 filas; limites de task via `CELERY_TASK_ANNOTATIONS` (`celery_settings.py:108-122`, não no decorator).
- **Sentry ao vivo:** `WORKER-9 Task failed` **689 ev** (culprit `apps.validation.tasks.extract.extract_data`) ilustra a falta de contexto por task.

### Veredito
**Parcial** — boa base (task_name/queue/tenant via `task_prerun`), mas falta `document_id` e a reclassificação de retry não é uniforme (boa em classification, genérica em ocr/entry).

### Plano de resolução
1. Extrair `document_id` de args/kwargs no `task_prerun` e setar como tag.
2. Replicar o padrão de `classification.py` (try/except específico → warning + retry, sem `capture_exception`) em `ocr.py` e `entry.py` para 429/5xx.
3. Garantir que retry não vire evento de erro (revisar `before_send` e o handler `task_retry`).

---

## Item 11 — Revisar módulo `@sentry/nextjs` no Frontend
`Camada: Frontend · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Adicionar `beforeSend`/`ignoreErrors`/`denyUrls` (hoje inexistentes), reduzir PII no Session Replay e remover as páginas de exemplo do wizard.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - **Sem** `beforeSend` / `ignoreErrors` / `denyUrls` nos **dois** frontends (grep = 0 ocorrências).
  - Páginas de exemplo **presentes** em ambos: `pages/sentry-example-page.tsx` + `pages/api/sentry-example-api.ts` (org hardcoded `automind-teste`, ex. linha 54; a rota API lança `SentryExampleAPIError`).
  - `next.config.js` org/project default `automind-teste`/`javascript-nextjs` (`AutoChecker_Frontend:40-42`, `AutoChecker/frontend:34-36`). `@sentry/nextjs ^10.43.0`.
  - Sem filtro de extensão de browser nem de 401/403.
- **Documentação:** §4/§8 (sub-instrumentado; defaults de teste).
- **Sentry ao vivo (12/06):** frontend tem **6 issues** unresolved (snapshot dizia 2) — e são **exatamente ruído filtrável**:
  | Issue | Mensagem | Eventos | Culprit |
  |---|---|---|---|
  | FRONTEND-3 | FirebaseError: Messaging…unsupported-browser | 18 (18 users) | `/login` |
  | FRONTEND-4 | FirebaseError: Messaging…unsupported-browser | 17 | `/external/register` |
  | FRONTEND-2 | `t.with` | 9 | `getInitialProps (/_error)` |
  | FRONTEND-6 | Invariant: attempted to hard navigate to the same URL | 1 | `/` |
  | FRONTEND-5 | Object Not Found Matching Id…MethodName:update | 1 | `/aceitar-convite/complete` |
  | FRONTEND-1 | Failed to connect to MetaMask | 1 | `/admin` |

### Veredito
**Não cumprida** (confere). Confirmado nas 3 fontes — e o ruído atual do frontend prova a necessidade dos filtros.

### Plano de resolução
1. **`ignoreErrors`:** `FirebaseError …unsupported-browser`, `Failed to connect to MetaMask`, `Object Not Found Matching Id` (ruído real medido). **`denyUrls`:** extensões de browser. **`beforeSend`:** descartar 401/403 esperados.
2. Remover `sentry-example-page.tsx` e `api/sentry-example-api.ts` dos dois frontends.
3. Reduzir PII no replay (cruza item 7) e corrigir org/project default de teste (cruza item 2). Aplicar no frontend produtivo.

---

## Item 12 — Estender cobertura Sentry aos serviços sem instrumentação
`Camada: AutoChecker · Esforço: G · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Instrumentar OCR (FastAPI/Textract), AIAgent (FastAPI + Celery próprio) e APP (Expo/RN); corrigir o Custos; decidir projeto próprio vs tag.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - **OCR** (`AutoChecker_OCR`): sem Sentry (requirements sem `sentry-sdk`; nenhum init).
  - **AIAgent** (`AutoChecker_AIAgent`): sem Sentry; **Celery próprio** isolado (`agent/config/celery_config.py:14` → `Celery("autochecker_agent", …)`), broker Redis próprio — não é o `autochecker-worker`.
  - **APP** (`AutoChecker_APP`): sem `@sentry/react-native` no `package.json`; **push é mock** (`src/features/notifications/hooks/useNotifications.ts`) → as issues de push **não vêm do APP**.
  - **Custos** (`AutoChecker_Custos`): tem `@sentry/nestjs ^10.43.0`; `src/instrument.ts:10` lê `SENTRY_DSN` (**correto**); typo `SENTRY_DNS` está **só na doc** `CLAUDE.md:98`; `sendDefaultPii:true` (`instrument.ts:12`); **sem projeto Sentry dedicado** (org/project vêm de env, não hardcoded).
- **Documentação:** §1/§5 confirmam (OCR/AIAgent/APP sem Sentry; Custos com DSN ambíguo/sem projeto).
- **Sentry ao vivo (12/06):** `find_projects("autochecker")` na org `automind-qd` retorna **apenas 3 projetos** — `autochecker-backend`, `autochecker-frontend`, `autochecker-worker`. **Nenhum** para OCR/AIAgent/APP/Custos. Lacuna confirmada.

### Veredito
**Não cumprida** (confere). Confirmado nas 3 fontes; a correção REV 10/06 (typo do Custos é de doc, não de código) está certa.

### Plano de resolução
1. Decidir **projeto Sentry dedicado vs tag** em projeto existente, por serviço.
2. Instrumentar OCR (`sentry-sdk[fastapi]`), AIAgent (FastAPI + `CeleryIntegration` do worker próprio), APP (`@sentry/react-native`).
3. Custos: **corrigir a doc** `CLAUDE.md:98` (`SENTRY_DNS`→`SENTRY_DSN`), criar projeto dedicado, `sendDefaultPii:false`.

---

## Item 13 — Documentar política de envio de eventos por camada
`Camada: AutoChecker · Esforço: P · Status: Não iniciado · Veredito: Não cumprida · Confiança: Parcial`

### O que a etapa exige
Critério de captura por camada (backend/worker/frontend) e nível mínimo por ambiente (DEV info+debug, STG info+warning+error, PRD warning+error); definir o que é erro vs evento esperado.

### O que cada fonte mostrou
- **Código:** cross-check — o frontend do AutoChecker **não tem** `beforeSend` (grep = 0 nos dois frontends) → não copiar config do Questionário.
- **Documentação:** **(REV 10/06)** `Questionario_Sentry_Respostas_Dev_2026-05.md` é multi-produto e descreve o **AutoLoad V4/EdgeGateway** (MQTTWorker, gatewayId, `api.ts` com beforeSend) — usar só para pendências transversais (release, alertas no painel); **não** copiar níveis/config do V4.
- **Sentry:** não aplicável.

### Veredito
**Não cumprida**. É entrega **documental** (não há artefato de código a "consertar"); a base já existe (reclassificações mapeadas nas Ondas 0–2).

### Plano de resolução
1. Escrever 1 doc de política: captura por camada (backend/worker/frontend), níveis por ambiente, e a definição "erro vs evento esperado".
2. Ancorar nas reclassificações já mapeadas: retries (item 10), auth por endpoint (item 6), UNAVAILABLE de sites (item 27).
3. **Não** copiar níveis/config do AutoLoad V4 (Questionário) — usá-lo só para pendências transversais.

### Ressalva
Os níveis exatos enviáveis por ambiente (o que é "info/debug" que vale enviar) dependem de **decisão do time** → essa parte fica **Parcial** até a política ser acordada.

---

### Resumo — Onda 1

| # | Etapa | Veredito (situação real) | Confiança |
|---|---|---|---|
| 9 | Tags + captura no Backend | **Parcial** — tags existem; **duplicação confirmada** (DjangoIntegration + middleware) a resolver | Sei |
| 10 | Tags + retries no Worker | **Parcial** — `task_prerun` seta quase tudo; falta `document_id` e reclassificação uniforme de retry | Sei |
| 11 | Revisar @sentry/nextjs | **Não cumprida** — sem beforeSend/ignoreErrors/denyUrls; páginas de exemplo em prod; 6 issues de ruído ao vivo | Sei |
| 12 | Estender cobertura | **Não cumprida** — só 3 projetos na org; OCR/AIAgent/APP/Custos cegos | Sei |
| 13 | Política por camada | **Não cumprida** — entrega documental; não copiar do V4 | Parcial |

---

# ONDA 2 — Contexto e Agrupamento
**Pipeline de documentos · Sem 4–6**

---

## Item 14 — Instrumentar o pipeline de documentos (6 estágios) com breadcrumbs + tags
`Camada: Worker · Esforço: G · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Adicionar tags `document.id`/`document.type`/`stage` e breadcrumbs por etapa do pipeline (Entry → OCR → Classificação → Extração → Autenticação → Integração) para saber **onde** travou e **quanto** cada etapa levou.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - **5 estágios encadeados** via `transaction.on_commit` + `apply_async`:
    - entry → ocr: `entry.py:35-40`
    - ocr → classification: `ocr.py:445-450`
    - classification → extract: `classification.py:286-291`
    - extract → authenticate: `extract.py:409-414`
  - A **Integração não é um 6º `apply_async`**: é disparada **dentro** da task de auth via `_send_document_processed_webhook(doc)` (`authenticator.py:201`) + `EntityWebhookService.notify_entity_on_authentication_complete(doc, doc.tenant)` (`authenticator.py:154/203`; função em `:566-680`) — **síncrono** ao fim da autenticação.
  - **Instrumentação Sentry no pipeline: ZERO.** 0 `sentry_sdk.add_breadcrumb`, 0 `set_tag('stage'/'document.id'/'document.type')`, 0 `set_context` nas tasks de `validation/tasks/`. Só `logger.info` (`entry.py:25,42`; `ocr.py:74-79,441-443`; `classification.py:170,349`; `authenticator.py:216-217`).
  - `Document.TYPE_CHOICES` em `shared/models/upload.py:324-342` — **17 tipos**.
- **Documentação:** §2.3 — 6 estágios encadeados, 11 filas, 17 tipos de documento.
- **Sentry ao vivo:** `WORKER-9 Task failed` **689 ev** é o sintoma — hoje não dá para saber em qual etapa o documento parou.

### 🔎 Achado novo — a autenticação NÃO é 100% scraping Selenium
A nota REV 10/06 do xlsx diz "auth = scraping Selenium (não provider OAuth SERPRO)". No código, isso vale para CIV/CIPP/CTPP/CVV/Cronotacógrafo/CR/MR (via `scraping_call` → `SCRAPING_URL`, ex. `scraper_client.py:48`), mas a **CNH usa SERPRO OAuth2**: `cnh.py:18` → `SERPRO_DECODE_URL = "https://gateway.apiserpro.serpro.gov.br/viodec/v1/decode"`; `cnh.py:33` → `_call_serpro_decode(qr_payload)`. Ao instrumentar a etapa de autenticação, tratar os **dois** caminhos (scraping e SERPRO) como spans/sub-etapas distintas.

### Veredito
**Não cumprida** (confere com "Não iniciado"). O pipeline existe e é rastreável no código, mas **nenhuma** instrumentação Sentry por etapa.

### Plano de resolução
1. Setar `document.id` e `document.type` como tags no `task_prerun` (cruza item 10) e `stage` por task.
2. `sentry_sdk.add_breadcrumb` no início/fim de cada estágio (com duração) — entry, ocr, classification, extract, authenticate.
3. **Instrumentar a Integração à parte** (não está na cadeia `on_commit`; é síncrona dentro da auth) — span próprio no webhook/dispatcher.
4. Tratar CNH (SERPRO) e demais tipos (scraping) como sub-etapas distintas da autenticação.

---

## Item 15 — Fingerprint customizado para issues genéricas e de alta cardinalidade
`Camada: Worker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Agrupar `Task failed` (sem contexto) por **task+causa**; remover o UUID do título de "Erro na geração do relatório <uuid>" e "Preferência <uuid> não encontrada" via fingerprint estável.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - **Nenhum fingerprint customizado** no código (os `before_send` não mexem em `fingerprint`; grep = 0).
  - "Task failed" é título **literal fixo** em `worker/config/celery_logging.py:145` (handler `task_failure` `:130-159`) — enriquece com `extra` (task_name, exception), mas o título é sempre o mesmo → agrupamento ruim.
  - UUID interpolado no título: `shared/tasks/report_tasks.py:392` → `"❌ Erro crítico na geração do relatório {preference_id}: {str(exc)}"`; `:143` → `"❌ Preferência {preference_id} não encontrada em nenhum tenant"` (+ `:139` debug). Cada `preference_id` único vira uma issue → alta cardinalidade.
- **Documentação:** §7 — WORKER-9 (Task failed) e os títulos com UUID listados como alta cardinalidade.
- **Sentry ao vivo:** `WORKER-9` **689 ev**; `WORKER-K` *relatório <uuid>* **242 ev**; `WORKER-N` *Preferência <uuid>* **241 ev**.

### Veredito
**Não cumprida**. Bom que não há fingerprint "errado"; ruim que a fragmentação (UUID no título) e a genérica ("Task failed") continuam.

### Plano de resolução
1. `Task failed`: fingerprint estável por `[task_name, exception_type]` no `before_send` (ou no handler), em vez do título único.
2. Relatório/Preferência: fingerprint fixo (ex.: `["report-generation-error"]`) e mover o UUID para **tag/context**, não para o título. Idealmente também ajustar as mensagens em `report_tasks.py:392/143` para não interpolar o UUID no título.

---

## Item 16 — Capturar erros silenciosos: composition service, webhooks e expiração de tenants
`Camada: Backend/Worker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Adicionar `sentry_sdk.capture_exception` nos blocos de `composition.py`, nos 3 webhooks de composição e na task `check_expired_tenants` (billing/suspensão). Fora do middleware HTTP, nenhum except de negócio reporta ao Sentry hoje.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - `shared/services/composition.py`: **17 except / 17 logger.error(.exception) / 0 capture** — confere a REV 10/06 (14 `except Exception` + 2 `requests.exceptions.*` + 1 `(TypeError, ValueError)`). Exemplos: `:147`, `:276`, `:432`, `:1425-1435` (webhooks de entidade com `Timeout`/`ConnectionError`).
  - 3 webhooks em `backend/apps/composition/views.py`: `_send_composition_created_webhook` (`:874`; `logger.error` `:941`), `_send_composition_updated_webhook` (`:991`; `logger.error` `:1056-1058` + `logger.exception` `:1059`), `_send_composition_deleted_webhook` (`:1109`; `logger.error` `:1175-1176`) — todos **só logam**, nenhum manda ao Sentry. (As linhas do xlsx 940/1055/1174 batem com os `logger.error` reais 941/1056/1175.)
  - `check_expired_tenants` em `backend/apps/tenants/tasks.py:10-38`: `except` `:34`, `logger.error` `:35`, **sem** capture.
  - **Busca global:** `sentry_sdk.capture_exception` existe em **1 só lugar** — `backend/config/middleware/api_logging.py:40`. Worker e shared: 0.
- **Documentação:** §6 — "fora do middleware HTTP, **nenhum** except de negócio chama `capture_exception`".
- **Sentry ao vivo:** falhas de webhook que hoje só logam aparecem como `WORKER-1R/1Q` (HTTP 404, ~135 ev cada) por virem da task de notificação (`process_notification_task`), não dos webhooks de composição.

### Veredito
**Não cumprida**. Premissa confirmada nas 3 fontes (1 único `capture_exception` em toda a base).

### Plano de resolução
1. Adicionar `capture_exception` (com tags de contexto) nos except relevantes de `composition.py`, nos 3 webhooks (`views.py:941/1056/1175`) e em `check_expired_tenants` (`tenants/tasks.py:35`).
2. Distinguir erro de negócio **permanente** (capturar) de **transiente esperado** (warning/retry) para não inflar.
3. **Cuidado com item 9:** não recapturar o que o middleware HTTP já pega — evitar dupla contagem.

---

### Resumo — Onda 2

| # | Etapa | Veredito (situação real) | Confiança |
|---|---|---|---|
| 14 | Instrumentar pipeline (breadcrumbs+tags) | **Não cumprida** — 0 instrumentação por etapa; integração fora da cadeia `on_commit`; **CNH usa SERPRO**, não scraping | Sei |
| 15 | Fingerprint customizado | **Não cumprida** — sem fingerprint; "Task failed" genérico (689 ev) + UUID no título (K/N ~240 ev cada) | Sei |
| 16 | Capturar erros silenciosos | **Não cumprida** — `composition.py` 17 except / 0 capture; único `capture_exception` da base é `api_logging.py:40` | Sei |

---

# ONDA 3 — Alertas + Health Checks
**Beat e filas · Sem 6–8**

---

## Item 17 — Definir níveis N1/N2/N3 e responsáveis por alerta
`Camada: AutoChecker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Parcial`

### O que a etapa exige
Mapear quem recebe qual alerta por nível (N1 = triagem, N2 = técnico, N3 = especialista/engenharia) **antes** de ativar qualquer notificação. É o **gate** da política de alertas.

### O que cada fonte mostrou
- **Código:** nada a auditar — decisão organizacional, não vive em código.
- **Documentação:** `Roadmap_Observabilidade_AutoChecker.md` (Etapa 17) marca o mapeamento como **[PENDENTE: organização]** ("o mapeamento N1/N2/N3 não existe nas fontes"); manda "espelhar a decisão do AutoLoad", mas **essa decisão do AutoLoad também está pendente**. Nenhuma outra doc (`AutoChecker-documentacao.md`, `Questionario_…`, `Oportunidades…`) define os níveis.
- **Sentry:** não aplicável.

### Veredito
**Não cumprida.** É um **bloqueio organizacional**: sem o mapa N1/N2/N3, os itens 18 (regras) e 21 (roteamento) não têm destinatário.

### Plano de resolução
1. Decidir e documentar o mapa: quem é N1/N2/N3 por produto e qual nível recebe qual classe de alerta.
2. Tratar como pré-requisito (gate) dos itens 18 e 21.

### Ressalva
O "como resolver" depende de **decisão do time** — não é dado extraível do código. Confiança **Parcial** (a inexistência está confirmada; o conteúdo da decisão, não).

---

## Item 18 — Configurar regras de alerta com filtro `environment:production`
`Camada: AutoChecker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei (live: Parcial)`

### O que a etapa exige
Threshold (ex.: 50 ocorrências/5min), ciclo de supressão, alerta de regressão (resolved→unresolved) e roteamento por nível. Excluir o schema público. Hoje há só 1 regra default, sem filtro de ambiente.

### O que cada fonte mostrou
- **Código:** nada — regras vivem só no painel Sentry.
- **Documentação:** `AutoChecker-documentacao.md` §6 — "Apenas 1 regra default (*high priority issues*), **sem filtro de ambiente** (`env=None`)".
- **Sentry:** o MCP disponível **não expõe tool de regras de alerta** → o estado da regra não foi verificável ao vivo; baseado na doc/snapshot. Depende do `environment` saneado (Onda 0/item 1).

### Veredito
**Não cumprida.** Uma regra sem filtro de ambiente equivale, na prática, a não ter alerta acionável.

### Plano de resolução
1. Criar regras com filtro `environment:production`, threshold (ex.: 50/5min), ciclo de supressão e **alerta de regressão** (resolved→unresolved).
2. Roteamento por nível (depende do item 17). Excluir o schema `public` (cruza itens 4 e 8).

### Ressalva
Pré-requisito: o `environment` tem de estar confiável (item 1) — alertar sobre base não saneada gera falso-positivo.

---

## Item 19 — Garantir `SoftTimeLimitExceeded` no Sentry + timeout no microserviço OCR
`Camada: Worker · Esforço: P · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Os limites Celery já existem; garantir que `SoftTimeLimitExceeded` seja **capturado** no Sentry, cobrir tasks sem annotation, e tratar o microserviço OCR (FastAPI) que faz polling do Textract em `while True` **sem timeout**.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Limites globais: `CELERY_TASK_TIME_LIMIT = 1200` / `CELERY_TASK_SOFT_TIME_LIMIT = 900` (`worker/config/settings/celery_settings.py:18-19`).
  - `CELERY_TASK_ANNOTATIONS` (`celery_settings.py:107-143`): `run_textract` 600/480, `authenticate` 900/720, `classify_document` 300/240, `reprocess_document(s)` 600/480, `generate_user_scheduled_report` 600/480, `collect_sites_availability` 600/480.
  - **`SoftTimeLimitExceeded` NÃO é tratado** em lugar nenhum (grep = 0); o handler `task_failure` (`worker/config/celery_logging.py:129-159`) o trata como exceção qualquer (passa batido).
  - **~10 tasks sem annotation** rodam só no limite global: `entry.process_document_validation`, `extract.extract_data`, `check_expired_tenants`, `recalculate_document_validity`, `process_notification_task`, `retry_failed_notifications`, `generate_scheduled_reports`, `process_integration_task`, etc.
  - **OCR:** `AutoChecker_OCR/ocr_service.py:85-104` — `while True` chamando `textract.get_document_text_detection(...)` **sem `timeout=`** (boto3 sem `botocore.config.Config` de read/connect timeout) → request pendura indefinidamente.
- **Documentação:** §2.3 (limites via `CELERY_TASK_ANNOTATIONS`, não no decorator); §5 (OCR polling em `while True` sem timeout; backoff fixo `sleep(5–20s)`).
- **Sentry ao vivo (12/06):** busca por `SoftTimeLimitExceeded` no worker → **nenhuma issue**. Ou não dispara, ou é absorvida no genérico `WORKER-9 Task failed` (sem fingerprint, item 15).

### Veredito
**Não cumprida.** Os limites existem, mas falta a **captura explícita** do soft-timeout e o OCR tem polling sem teto.

### Plano de resolução
1. Tratar `SoftTimeLimitExceeded` explicitamente (capturar com tag de `task_name`/etapa) no handler `task_failure` ou nas tasks críticas.
2. Adicionar annotation (ou limite explícito) às ~10 tasks que hoje só caem no global.
3. Pôr **timeout** no polling do OCR: `botocore.config.Config(read_timeout=…, connect_timeout=…)` + teto de tempo/iterações no `while True`.

---

## Item 20 — Health checks + Uptime + Cron Monitors (Beat e filas)
`Camada: Backend/Worker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Tornar `/api/core/healthcheck/` um readiness **real** (usar o `django-health-check` já instalado) **antes** de criar o Uptime Monitor; Cron Monitors para o Beat e heartbeat das 11 filas.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Healthcheck **trivial**: `apps/core/views.py:19-22` → `Response({"status": "ok"})` (não checa DB/Redis/broker).
  - `django-health-check==3.17.0` em `backend/requirements.txt:23`, mas **fora** de `INSTALLED_APPS` e **não** plugado na rota (a rota `apps/core/urls.py:12` aponta para a view trivial).
  - **Beat divergente:** `worker/config/celery.py:69-111` define **8 jobs** e **sobrescreve** o `beat_schedule` de `worker/config/settings/celery_settings.py:31-63` (**6 jobs — mortos**). 2 jobs existem **só** em `celery.py` (notify subscribers / non-subscribers expiring documents). Divergências: `recalculate-document-validity` 00:15 (celery.py) vs 00:00 (settings); `collect_sites_availability` 60min vs `crontab(minute=0)`.
  - **11 filas** (`celery_settings.py:68-105`).
- **Documentação:** §2.1 (`django-health-check` instalado), §6 (health "falsa"), §2.3 (divergência beat 8 vs 6; 11 filas).
- **Sentry:** Uptime/Cron Monitors não verificáveis pelo MCP disponível.

### 🔎 Achados — health "falsa" + dois beat schedules
(1) O healthcheck retorna `ok` sem checar dependências — um Uptime Monitor sobre ele daria "verde" mesmo com DB/Redis fora. (2) Há **dois** `beat_schedule`; o de `celery.py` (8 jobs) vence e o de `celery_settings.py` (6) fica morto — risco de job fantasma conforme qual settings carrega.

**Jobs do beat efetivo (8):** `check-expired-tenants-daily` (00:00), `recalculate-document-validity-daily` (00:15), `notify-subscribers-expiring-documents-daily` (08:00), `notify-non-subscribers-expiring-documents-daily` (08:30), `check-scheduled-reports` (hora cheia), `reprocess-failed-documents-nightly` (00:30), `collect_sites_availability` (60min), `integration-reauth` (*/5min).

### Veredito
**Não cumprida.** A base de health/monitoring está frágil (health falsa, beat duplicado).

### Plano de resolução
1. Tornar o healthcheck um **readiness real** com `django-health-check` (DB/Redis/broker) e só então criar o **Uptime Monitor**.
2. Consolidar o `beat_schedule` em um único lugar (matar o de settings) para acabar com jobs fantasma.
3. **Cron Monitors** para os 8 jobs efetivos (intervalos acima).
4. **Heartbeat** das 11 filas.

---

## Item 21 — Integração de alertas em canal (Slack/Teams) + ticket + CODEOWNERS
`Camada: AutoChecker · Esforço: M · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Plugar as regras num canal (Slack/Teams) e criar ticket automático; configurar CODEOWNERS por projeto Sentry. Hoje o único destino é e-mail genérico aos owners → o N1 não recebe nada automaticamente.

### O que cada fonte mostrou
- **Código (CONFIRMADO):** **sem arquivo `CODEOWNERS`** no repo (raiz/`.github/`/`.azuredevops/`/`docs/`). **Sem** integração Slack/Teams versionada — `backend.azure-pipelines.yml` (1–247) não tem; os hits de `webhook` no código são de negócio (composição/notificação), não de alerta Sentry.
- **Documentação:** §6/§7 + Roadmap (Etapa 21): "o único destino de alerta é e-mail genérico aos owners — o N1 não recebe nada automaticamente". CODEOWNERS por projeto = item novo (gap G10, Alta).
- **Sentry:** integração de canal vive só no painel — não versionada.

### Veredito
**Não cumprida.** Confirmado nas 3 fontes (sem canal, sem CODEOWNERS).

### Plano de resolução
1. Definir o canal oficial (Slack **ou** Teams), plugar as regras e criar ticket automático.
2. Criar `CODEOWNERS` por projeto Sentry para rotear a issue ao dono.
3. Depende do item 17 (gate N1/N2/N3) e do item 18 (regras com filtro de ambiente).

---

### Resumo — Onda 3

| # | Etapa | Veredito (situação real) | Confiança |
|---|---|---|---|
| 17 | Níveis N1/N2/N3 + responsáveis | **Não cumprida** — bloqueio organizacional; mapa não existe (Roadmap [PENDENTE]); AutoLoad também pendente | Parcial |
| 18 | Regras de alerta com filtro de ambiente | **Não cumprida** — 1 regra default, `env=None` (regras não consultáveis via MCP) | Sei (live: Parcial) |
| 19 | SoftTimeLimitExceeded + timeout OCR | **Não cumprida** — limites existem; sem captura de SoftTimeLimit; OCR `while True` sem timeout; ~10 tasks sem annotation | Sei |
| 20 | Health + Uptime + Cron Monitors | **Não cumprida** — health falsa; django-health-check instalado mas fora; beat 8 vencem / 6 mortos; 11 filas | Sei |
| 21 | Canal (Slack/Teams) + ticket + CODEOWNERS | **Não cumprida** — sem CODEOWNERS, sem canal versionado; só e-mail genérico → N1 não recebe | Sei |

---

# ONDA 4 — Logs Correlacionados + Tracing
**Performance, trace distribuído e correlação de logs · Sem 8–11**

---

## Item 22 — Resolver o N+1 e padronizar a amostragem de performance
`Camada: Backend · Esforço: M · Status: Não iniciado · Veredito: Parcial · Confiança: Sei (live)`

### O que a etapa exige
O tracing **já está ativo** — não é "ligar" performance. O que falta é (a) atacar a issue **N+1 Query** (`BACKEND-5`) e (b) padronizar a `traces_sample_rate` por ambiente.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - `traces_sample_rate` lido de env nos **3 serviços Python**, sempre default **0.2**: backend `backend/config/settings/base.py:733`, worker `worker/config/celery.py:27`, helper `shared/observability/sentry.py:33-35` (`float(os.environ.get("SENTRY_TRACES_SAMPLE_RATE","0.2"))`).
  - Frontend define `tracesSampleRate` **hardcoded por ambiente** (prod 0.2 / dev 1.0), **não** por env: `AutoChecker_Frontend/instrumentation-client.ts:14-15`, `sentry.server.config.ts:12-13`, `sentry.edge.config.ts:13-14`. O Custos lê de env (`AutoChecker_Custos/src/instrument.ts:3-4`).
  - **N+1 confirmado no código** em `/api/tenants/all-tenants-switcher/` → `backend/apps/tenants/views.py:907-997`. Dois caminhos: (1) superadmin itera `Tenant.objects.exclude(...)` sem `prefetch` (`views.py:938-948`); (2) não-superadmin faz `TenantMembership.objects.get(...)` **dentro** do loop de tenants + `schema_context` por iteração (`views.py:956-971`) → uma query por tenant.
  - Outro loop de risco: `backend/apps/portal/views.py:133-146` itera tenants chamando `get_usage_status(tenant)`.
- **Documentação:** xlsx REV 10/06 e ESTÁTICO #10 (ajustado: tracing já lê env; N+1 ao vivo 09/06 no switcher).
- **Sentry ao vivo (17/06):** issue **`AUTOCHECKER-BACKEND-5` "N+1 Query"** (culprit `/api/tenants/all-tenants-switcher/`) está **unresolved, 518 eventos** — o xlsx registrava **122** (**>4×**) —, 1ª vez 09/04, **última há ~30 min**, atribuída a Tarcisio. Além dela, **+6 issues N+1** que o xlsx não cita: `-7` `/api/entity/driver/` (21), `-6` `/api/entity/vehicle/` (20), `-1X` `/api/audit/logs/stats/` (16, recente), `-8` `/api/accounts/users/all_users/` (7), `-38` `/api/accounts/validate-invite/` (1), `-24` `/api/trial/admin/leads/` (1).

### 🔎 Achado — o N+1 não é um, são sete (e o principal cresceu 4×)
O cronograma trata o N+1 como item único (switcher, 122 ev). Ao vivo há **7 issues N+1 abertas**; a principal saltou para **518 ev** e continua disparando. driver/vehicle/all_users casam com os loops de queryset do código. Vale resolver **em lote**, não só o switcher.

### Veredito
**Parcial.** A amostragem de performance **já existe e funciona** (env, default 0.2) — esse pedaço está cumprido. Mas (a) o **N+1 não foi resolvido** (518 ev e subindo) e (b) a amostragem **não é diferenciada por ambiente** no backend/worker (default fixo 0.2; só o frontend separa prod/dev).

### Plano de resolução
1. Corrigir o N+1 do switcher: no caminho não-superadmin, trocar o `TenantMembership.objects.get()` por-tenant por um `filter(...).select_related('tenant','user')` único **fora** do loop; no superadmin, garantir que nada acesse FK lazy dentro do laço.
2. Estender a correção às outras 6 rotas (driver, vehicle, all_users, audit/logs/stats, validate-invite, trial/admin/leads) com `select_related`/`prefetch_related`.
3. Padronizar `traces_sample_rate` por ambiente também no backend/worker (ex.: prod 0.1–0.2, dev 1.0) via env por ambiente.
4. Após corrigir, **resolver** as issues no Sentry e habilitar alerta de regressão (cruza item 18).

### Ressalva
O frontend **hardcoda** a taxa (não usa env) — se a decisão for "tudo por env", isso também muda. Confiança **Sei** (código + issue ao vivo).

---

## Item 23 — Tracing distribuído Backend ↔ Worker (Celery) ↔ serviços auxiliares
`Camada: AutoChecker · Esforço: G · Status: Não iniciado · Veredito: Não cumprida · Confiança: Sei`

### O que a etapa exige
Propagar trace por toda a cadeia de tasks e nas chamadas HTTP ao scraping-server, ao OCR e a Textract/OpenAI como **spans**, para seguir um documento ponta a ponta. Pré-requisito: OCR e AIAgent precisam de Sentry primeiro (Onda 1, item 12).

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - **Cadeia de 5 estágios** via `transaction.on_commit(...)` + `apply_async(...)`: entry `worker/apps/validation/tasks/entry.py:35-40` (→ `run_textract`, fila `ocr_heavy`) → ocr `.../ocr.py:445-449` (→ `classify_document`, `ai_processing`) → classification `.../classification.py:286-287` (→ `extract_data`) → extract `.../extract.py:409-410` (→ `authenticate_document`) → authenticate `.../authenticator.py` (estágio final).
  - **Hop da INTEGRAÇÃO — DISCREPÂNCIA com o xlsx:** a nota REV diz que a integração "sai por signal/dispatcher a partir de `authenticator.py`". No código **não sai do authenticator**: é um **`post_save` em `NodeDocument`** (`shared/models/signals.py:303-308`) que, via `on_commit` (`signals.py:202` e `:252`), chama `IntegrationDispatchService.dispatch_driver_event(...)` → `process_integration_event.delay(...)` (`shared/services/integration_dispatch.py:96`). O gatilho é o **save da composição**, não o authenticator.
  - **Chamadas HTTP a auxiliares (viram spans):** scraping `worker/apps/validation/tasks/utils/scraper_client.py:62` (`requests.post`, timeout 160); Textract boto3 `.../ocr.py:22-27` + `:301-306`/`:312-316`/`:341-342`; OpenAI `.../classification.py:86`; (AIAgent→Evolution `AutoChecker_AIAgent/agent/tasks/message_tasks.py:202`, httpx).
  - **Cobertura ausente:** `AutoChecker_OCR` e `AutoChecker_AIAgent` **sem `sentry_sdk`** (grep recursivo = 0). Sem SDK, não há spans desses serviços.
  - **Propagação de trace HOJE:** **NÃO ENCONTRADA** — sem `continue_trace`/`sentry-trace`/`baggage`/`trace_propagation_targets` em lugar nenhum.
- **Documentação:** xlsx (ponto cego central; depende da cobertura da Onda 1).
- **Sentry:** trace distribuído entre serviços não verificável via MCP (sem spans de OCR/AIAgent hoje).

### Veredito
**Não cumprida.** O `CeleryIntegration` propaga trace backend→worker automaticamente, mas (a) os **hops HTTP** (scraping/OCR/Textract/OpenAI) não propagam contexto, (b) **OCR e AIAgent não têm SDK** e (c) o salto para a integração sai de um **signal de composição**, não do authenticator — instrumentar à parte.

### Plano de resolução
1. **Pré-requisito:** instrumentar OCR e AIAgent com Sentry (item 12) — sem isso não há spans.
2. Propagar trace nos hops HTTP: enviar headers `sentry-trace`/`baggage` no `scraper_client.py:62` e nas chamadas ao OCR; criar spans manuais em torno de Textract/OpenAI.
3. Instrumentar o hop da integração no ponto **real** (`signals.py:202/252` → `integration_dispatch.py:96`), propagando `trace_id` no `process_integration_event.delay`.
4. Validar uma trace ponta-a-ponta (entry→…→authenticate→integração) no Sentry.

### Ressalva
Esforço **G**, dependente da Onda 1. A correção da atribuição "authenticator.py" → "post_save de `NodeDocument`" deve ir ao cronograma. Confiança **Sei**.

---

## Item 24 — Correlacionar Loki/Promtail com Sentry (`trace_id`)
`Camada: Worker · Esforço: M · Status: Não iniciado · Veredito: Parcial · Confiança: Sei`

### O que a etapa exige
Os workers já emitem logs JSON para o Grafana Loki via Promtail. Incluir `trace_id`/`tenant_id` nos logs e linkar **Sentry↔Loki** para pular do erro ao log estruturado da mesma execução.

### O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - **Logs JSON existem:** `python-json-logger` (`requirements`), formatter `jsonlogger.JsonFormatter` em `worker/config/settings/base.py:181-184`; logger `celery.tasks` → `/var/log/celery/tasks.log` (`base.py:222-226`); handlers de task emitem `extra={task_name,task_id,status,queue,duration_ms,tenant,...}` (`worker/config/celery_logging.py`); backend `api_logging.py:70` faz `json.dumps`.
  - **Loki/Promtail existem:** `worker/promtail-config-dev.yml` e `promtail-config-prod.yml` (push p/ `https://monitor.autochecker.cloud/loki/api/v1/push`, job `celery-tasks`, coleta `/var/log/celery/*.log`, extrai task_name/status/queue/tenant/env/duration_ms); serviço `grafana/promtail:3.5.0` em `docker-compose.dev.yml:125-134` / `docker-compose.prod.yml:144-157`.
  - **`tenant_id` JÁ está nos logs** (`celery_logging.py:92/117/151/...`; backend payload `tenant`). **`trace_id` NÃO** — nada de `trace_id`/`sentry_trace`/`traceparent` nos formatters.
  - **`LoggingIntegration` do Sentry NÃO ligada** no init (`worker/config/celery.py:22-32`, `shared/observability/sentry.py`) — só Django/Celery/Redis.
- **Documentação:** xlsx (Loki/Promtail já existem; falta amarrar aos traces).
- **Sentry:** correlação não verificável via MCP.

### Veredito
**Parcial.** Metade do item **já está pronta** (logs JSON + Loki/Promtail + `tenant_id`); falta só o amarrador: **`trace_id` nos logs** e o link Sentry↔Loki. O xlsx marca "não iniciado" — na prática a infra já existe.

### Plano de resolução
1. Injetar `trace_id` (do scope Sentry, ex.: `get_traceparent`) e `schema_name` em todos os registros — via filter de logging que lê o scope do Sentry, alimentando o `extra` do `celery_logging.py` e o `api_logging.py`.
2. Adicionar `trace_id`/`tenant` como labels extraídos no Promtail (`promtail-config-*.yml`) para filtrar no Loki.
3. Configurar o link Sentry↔Loki (e, opcionalmente, `LoggingIntegration` para anexar breadcrumbs de log aos eventos).

### Ressalva
A correlação real depende de o `trace_id` ser o **mesmo** identificador nos dois lados — garantir que o valor logado seja o `trace_id` do evento Sentry (não um id interno). Confiança **Sei** no estado atual; o "como amarrar" é direto.

---

### Resumo — Onda 4

| # | Etapa | Veredito (situação real) | Confiança |
|---|---|---|---|
| 22 | N+1 + amostragem de performance | **Parcial** — tracing/amostragem já ativos (env, 0.2); N+1 NÃO resolvido (`BACKEND-5` 518 ev + 6 issues); taxa não diferenciada por ambiente no back/worker | Sei (live) |
| 23 | Tracing distribuído back↔worker↔auxiliares | **Não cumprida** — Celery propaga back→worker; hops HTTP sem propagação; OCR/AIAgent sem SDK; integração sai de `post_save`, não do authenticator | Sei |
| 24 | Loki/Promtail ↔ Sentry (`trace_id`) | **Parcial** — JSON+Loki+Promtail+`tenant_id` já existem; falta `trace_id` nos logs e link Sentry↔Loki; `LoggingIntegration` off | Sei |

---

## Consolidado — o que ficou Parcial / Não sei / a confirmar

- **Item 1:** distribuição de `environment` do frontend ("15% production") **não reproduzida** ao vivo via MCP (errors/30d ≠ all-events do snapshot).
- **Item 8:** total exato de issues abertas **hoje** não recontado por API (o fato "0 resolvidas" foi confirmado).
- **Item 13:** níveis exatos por ambiente dependem de **decisão do time**.
- **Item 14:** a nota REV do xlsx ("auth = scraping, não SERPRO") é **imprecisa** — a **CNH usa SERPRO OAuth2** (`cnh.py:18`); os demais tipos usam scraping.
- **Item 17:** a decisão N1/N2/N3 **não existe** (bloqueio organizacional, depende do time); "espelhar o AutoLoad" não ajuda — o AutoLoad também está pendente.
- **Itens 18/20/21:** regras de alerta, Uptime/Cron Monitors e integrações de canal vivem **só no painel Sentry** e **não são consultáveis pelo MCP** disponível — estado baseado em doc/snapshot.
- **Item 19:** nenhuma issue `SoftTimeLimitExceeded` ao vivo hoje — não dá para saber se não dispara ou se é absorvida no genérico "Task failed".
- **Item 22:** a nota do xlsx ("N+1 = 122 ev no switcher") está **defasada** — ao vivo (17/06) são **518 ev** só no switcher e **+6 issues N+1** em outras rotas; amostragem `traces_sample_rate` não é diferenciada por ambiente no back/worker.
- **Item 23:** o xlsx atribui o hop da integração a `authenticator.py`; o código mostra que sai de **`post_save` de `NodeDocument`** (`shared/models/signals.py:303-308`) — atribuição a corrigir no cronograma.
- **Item 24:** infra Loki/Promtail + `tenant_id` **já existem** (xlsx subestima como "não iniciado"); o gap real é `trace_id` nos logs + link Sentry↔Loki.
- **Global:** qual dos **dois frontends** é o produtivo — a confirmar com o time (afeta 1, 2, 7, 11).
- **Global:** o doc `Auditoria_Cronograma_vs_Codigo_AutoChecker_2026-06-10` citado no xlsx **não existe** nos repositórios.

## Mapa de dependências entre itens (para ordenar a execução)

- **Item 5 (consolidar init)** é base de **9** (dedup de captura), **10** (tags worker), **2/item release** e do `send_default_pii` do **7**.
- **Item 6 (corrigir health)** alimenta **20** (readiness real + Uptime/Cron monitors).
- **Item 4 (migrate_schemas)** e **item 8 (excluir schema public)** se cruzam nos alertas (**18**).
- **Item 10 (tags por task)** habilita **14** (`document.id`/`stage`) e **15** (fingerprint por task+causa).
- **Item 9 (dedup)** precisa ser combinado com **16** (novas capturas) para não dobrar eventos.
- **Item 2 (org/project + release)** e **item 11 (limpeza do frontend)** dependem de decidir o **frontend canônico** (ressalva global #2).
- **Item 17 (N1/N2/N3)** é gate de **18** (regras) e **21** (canal/CODEOWNERS) — sem o mapa de responsáveis, alerta não tem destinatário.
- **Item 1 (environment saneado)** é pré-requisito de **18** (filtro `environment:production`).
- **Item 6 (health real)** é pré-requisito de **20** (Uptime Monitor sobre readiness de verdade).
- **Item 12 (cobertura Sentry em OCR/AIAgent)** é pré-requisito de **23** (sem SDK não há spans desses serviços no trace distribuído).
- **Item 22 (resolver N+1)** alimenta **18** (alerta de regressão após resolver) e **26** (dashboard de latência por etapa).
- **Item 23 (trace_id ponta-a-ponta)** é pré-requisito de **24** (correlação Loki↔Sentry só faz sentido com `trace_id` propagado).

---

## Fontes

- **Código real** em `C:\Projetos\automind-obs\Produtos\Autochecker` (backend/worker/shared, frontend ×2, OCR, AIAgent, APP, Custos, Scrapping) — citações `arquivo:linha` verificadas em 12/06/2026 (Ondas 0–3) e **17/06/2026 (Onda 4: tracing, N+1, Loki/Promtail)**.
- **Documentação:** `AutoChecker-documentacao.md`, `Oportunidades de Melhoria de Observabilidade - AutoChecker.md` (14/04), `Roadmap_Observabilidade_AutoChecker.md`, `Questionario_Sentry_Respostas_Dev_2026-05.md`, `Auditoria_Observabilidade_AutoChecker_2026-06-03.md`.
- **Sentry:** org `automind-qd` (snapshot 04/05→03/06 do xlsx + verificação ao vivo via MCP em 12/06).
- **Análises por etapa:** `Etapa2_Release_SetCommits_Pipelines_AutoChecker.md`, `Etapa3_PeriodicTask_Orfa_Beat_AutoChecker.md`.

> **Próximo:** Onda 5 — Métricas de Negócio + Dashboard (itens 25–26). Depois Onda 6 — Endurecimento, Terceiros e Compliance (itens 27–31).
