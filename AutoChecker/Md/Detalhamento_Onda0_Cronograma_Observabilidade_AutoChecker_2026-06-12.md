# Detalhamento da Onda 0 — Como resolver cada etapa (Cronograma de Observabilidade · AutoChecker)

> **Escopo desta entrega:** Onda 0 — Saneamento da Base (o **GATE** do plano). Itens **1, 4, 5, 6, 7, 8**.
> Itens **2** e **3** já têm análise dedicada — ver `Etapa2_Release_SetCommits_Pipelines_AutoChecker.md` e `Etapa3_PeriodicTask_Orfa_Beat_AutoChecker.md` (apenas referenciados aqui, não reescritos).
>
> **Data da análise:** 2026-06-12
> **Regra adotada:** nada de informação inventada. Cada afirmação vem de **código (`arquivo:linha`)**, **documentação** ou **Sentry ao vivo**. Onde as 3 fontes não bastam, está marcado **Parcial** ou **Não sei**.

## Fontes consultadas

| Fonte | Localização | Uso |
|---|---|---|
| **Código real** | `C:\Projetos\automind-obs\Produtos\Autochecker\` (monorepo `AutoChecker\` = backend/worker/shared/frontend + serviços `AutoChecker_Frontend`, `_OCR`, `_AIAgent`, `_APP`, `_Custos`, `Scrapping`) | citações `arquivo:linha` verificadas em 12/06 |
| **Documentação** | `Estudo de melhoria de observabilidade\AutoChecker-documentacao.md` (e cópia em `Cronograma observabilidade\AutoChecker\`); `Oportunidades de Melhoria...AutoChecker.md` (ESTÁTICO 14/04) | corroboração técnica |
| **Sentry (MCP)** | org **`automind-qd`** · projetos `autochecker-backend` / `-worker` / `-frontend` | validação ao vivo (12/06) |

### Ressalvas globais (valem para todos os itens)

1. **Doc de auditoria citado no xlsx não existe como arquivo.** O cronograma atribui as revisões "REV 10/06" a `Auditoria_Cronograma_vs_Codigo_AutoChecker_2026-06-10`, **que não está em nenhum dos repositórios** (só existe a `Auditoria_Observabilidade_AutoChecker_2026-06-03`). As notas REV estão dentro do próprio xlsx e foram revalidadas direto no código nesta análise.
2. **Dois frontends coexistem** com configs Sentry idênticas: `AutoChecker_Frontend\` (repo dedicado) e `AutoChecker\frontend\` (dentro do monorepo) — doc §4 confirma. **Qual está em produção precisa ser confirmado com o time** (impacta itens 1, 7, 11). Toda correção de frontend tem de ser aplicada no que realmente faz deploy.
3. **Semanas são relativas** (Sem 1–16), sem datas-âncora; **responsáveis "A definir"** em todos os itens.
4. **Divergência snapshot × ao vivo:** os percentuais de `environment` do xlsx vêm do snapshot 04/05→03/06 sobre **todos os eventos**. Minha checagem ao vivo (12/06) é **errors / 30d** e dá números diferentes (ver item 1) — não é contradição, é janela/métrica diferente.

---

## Item 1 — Padronizar tag `environment` nos 3 SDKs + isolar DEV/PRD

**Onda 0 · Frontend/Worker · Esforço M · Sem 1 · Status no cronograma: Concluído**

### a) O que a etapa exige
`environment ∈ {production, staging, development}` corretamente preenchido em backend, worker e frontend; isolar o ambiente dev local do projeto produtivo. KPI: ≥99% dos eventos com environment correto em 7 dias.

### b) O que cada fonte mostrou
- **Código (CONFIRMADO):** os 3 SDKs leem env var com fallback `"development"`:
  - Backend `backend/config/settings/base.py:730` → `environment=os.environ.get("SENTRY_ENVIRONMENT", "development")`
  - Worker `worker/config/celery.py:24` → idem
  - Frontend `instrumentation-client.ts:9`, `sentry.server.config.ts:9`, `sentry.edge.config.ts:10` → `process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development"`
  - Isolamento por **guard de DSN**: backend/worker `shared/observability/sentry.py:16-18` (`if not dsn: return`); frontend `enabled: !!NEXT_PUBLIC_SENTRY_DSN`. Não há DSN diferente "hard-coded" por ambiente — depende de variável de ambiente bem setada no deploy.
- **Documentação:** §7 confirma a causa do problema no frontend ("fallback `development` → DEV poluindo prod") e os percentuais do snapshot (backend 96%, frontend 15%, worker 65%).
- **Sentry ao vivo (12/06, errors / 30d):**
  - backend: production **11.458** / staging 54 → ~99,5% production
  - worker: production **725** / staging 28 → ~96% production
  - frontend: production **27** / staging 8 → ~77% production (sem `development` no dataset de **errors**; só 35 erros no total)

### c) Veredito
**Parcial.** O **código já padroniza** environment com fallback — o lado de código da etapa está feito (condiz com "Concluído"). Mas o **isolamento real depende do deploy** setar `*_SENTRY_ENVIRONMENT` corretamente, e o fallback `development` continua sendo a porta de poluição se a env var faltar. O ganho só é "fechado" quando o KPI ≥99% for medido na janela produtiva.

### d) Plano concreto
1. Garantir no CI/CD (4 pipelines Azure) que `SENTRY_ENVIRONMENT` (backend/worker) e `NEXT_PUBLIC_SENTRY_ENVIRONMENT` (frontend) sejam **sempre** setados — nunca cair no fallback. Considerar **falhar o build** se a var estiver vazia em prod.
2. Confirmar **qual frontend** faz deploy (ressalva global #2) e aplicar lá.
3. Bloquear máquina dev de enviar ao projeto produtivo: DSN de dev separado (ou `enabled:false`/sem DSN em dev).
4. Medir o KPI ≥99% sobre **todos os eventos** na janela de 7 dias, por projeto.

### e) Ressalvas
- O número "15% production" do xlsx **não foi reproduzido** ao vivo via MCP no dataset de **errors/30d** — para reproduzir seria preciso a distribuição de **todos os eventos** (transactions/replay) na janela do snapshot, que o dataset de errors não entrega diretamente. Logo, o "como está hoje" do frontend fica **Parcial**.

### f) Confiança: **Parcial** (código: Sei; número de environment ao vivo: Parcial).

---

## Item 2 — Release `<comp>@<hash>` + set-commits + isolar pipelines Azure

**Status no cronograma: Em andamento** — ❑ **Já analisado em detalhe.**
➡ Ver **`Etapa2_Release_SetCommits_Pipelines_AutoChecker.md`** (org/project de teste no `next.config.js`, suspect commits, isolamento de pipelines). Não reanalisado aqui por decisão de escopo.

---

## Item 3 — Limpar PeriodicTask órfã do Beat (`KeyError process_scheduled_notifications`)

**Status no cronograma: Pendente** — ❑ **Já analisado em detalhe.**
➡ Ver **`Etapa3_PeriodicTask_Orfa_Beat_AutoChecker.md`**. Achado-chave: a órfã provavelmente está no **arquivo `/tmp/celerybeat-schedule` (PersistentScheduler)**, não no DB `django-celery-beat` como o xlsx assume — verificar os dois. Não reanalisado aqui.

---

## Item 4 — Corrigir migrações faltando em schemas de tenant (`relation does not exist`)

**Onda 0 · Worker · Esforço M · Sem 1–2 · Status: Não iniciado**

### a) O que a etapa exige
Trocar o `migrate` simples do deploy por `migrate_schemas` e adicionar **gate** que falha o deploy se houver migração pendente em **qualquer** schema. O gap real é o **drift de tenants PRÉ-EXISTENTES**, que não recebem migrações novas.

### b) O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Deploy roda `migrate` simples: `backend/scripts/deploy.sh:97` (`python manage.py migrate --settings=config.settings.production`) e `backend.azure-pipelines.yml:148` (`migrate --plan`) / `:157` (`migrate`).
  - `migrate_schemas` só aparece em: `backend/apps/tenants/signals.py:12` **e `worker/apps/tenants/signals.py:12`** (migra tenant **novo** na criação, dentro de `if created:`) e `backend/scripts/reset_db_django.py:126` (`migrate_schemas --shared`, fora do deploy regular).
  - **Não há** nenhum management command de "check drift" nem gate de migração pendente no deploy → tenants pré-existentes ficam órfãos de migração.
- **Documentação:** §2.2 confirma textualmente ("deploy roda `migrate`/`migrate --plan` … nunca `migrate_schemas` … não há gate de migração por schema").
- **Sentry ao vivo (12/06):** cluster vivo e grande — `WORKER-1G` *relation "notifications_notificationlog" does not exist* **544 ev** (culprit `shared.tasks.notification_tasks.retry_failed_notifications`); `WORKER-C` *relation "notifications_reportpreference" does not exist* **153 ev**. (Snapshot xlsx: ~57 issues / ~1.267 ev.)

### c) Veredito
**Não cumprida** (confere com "Não iniciado"). A premissa do xlsx está **correta e confirmada na 3 fontes**, com a correção REV 10/06 (migrate_schemas também em `signals.py`) validada — e **mais**: existe nas duas cópias (backend e worker).

### d) Plano concreto
1. No deploy (`deploy.sh:97` + `backend.azure-pipelines.yml:148/157`) trocar `migrate` por **`migrate_schemas`** (aplica em public + todos os tenants). Avaliar `migrate_schemas --executor multiprocessing` para tempo de deploy.
2. **Gate de drift:** passo no pipeline que roda `migrate_schemas --check` (ou `migrate --check` por schema) e **falha** se houver migração não aplicada em qualquer schema.
3. Backfill único nos tenants pré-existentes em drift (rodar `migrate_schemas` manual/controlado antes de ligar o gate).
4. Excluir o schema `public` dos alertas que medem esse erro (cruza com item 8).

### e) Ressalvas
- `migrate_schemas` em produção multi-tenant é operação pesada/long-running — planejar janela e idempotência.

### f) Confiança: **Sei** (código + doc + Sentry concordam).

---

## Item 5 — Consolidar init do Sentry no helper `init_sentry` (+ CeleryIntegration no backend)

**Onda 0 · Backend/Worker · Esforço P · Sem 2 · Status: Não iniciado**

### a) O que a etapa exige
Backend e worker fazem `sentry_sdk.init` **direto** e divergem; o helper `shared/observability/sentry.py` existe mas ninguém chama. Migrar ambos para `init_sentry(service)`. **Atenção (REV 10/06):** o helper só dá `CeleryIntegration` quando `service=='worker'` — **trocar só a chamada não dá CeleryIntegration ao backend**; é preciso alterar o helper.

### b) O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - Backend init inline `base.py:728-736`: integrations `[DjangoIntegration(), RedisIntegration()]` (**sem Celery**), `before_send=_sentry_before_send` (filtra `/health/` e ruído transiente de Redis, `:713-723`).
  - Worker init inline `worker/config/celery.py:22-32`: `[DjangoIntegration(), CeleryIntegration(), RedisIntegration()]`, `before_send` = lambda que **só** filtra `/health/` (**sem** scrubbing de breadcrumb).
  - Helper `shared/observability/sentry.py:9-38`: adiciona `CeleryIntegration` **apenas** se `service_name == "worker"` (`:25-26`); `before_send_filter` (`:41-51`) faz **scrubbing de query nos breadcrumbs** (`:46-49`) — proteção que o init inline do worker **não** tem.
  - `init_sentry(` **nunca é chamado** em produção — só em `shared/observability/tests/test_sentry.py`. Confirmado por busca global.
- **Documentação:** §6 ("helper … não é chamado por ninguém → config duplicada e drift") e §6 confirmam os dois inits e a ausência de Celery no backend.
- **Sentry:** não aplicável diretamente (questão de configuração de SDK).

### c) Veredito
**Não cumprida** (confere com "Não iniciado"). A correção REV 10/06 do xlsx está **certa**: o helper hoje **não daria** CeleryIntegration ao backend.

### d) Plano concreto
1. **Alterar o helper** `init_sentry` para dar CeleryIntegration ao backend também (o backend Django enfileira tasks → eventos de Celery são úteis), ou parametrizar as integrations explicitamente por serviço.
2. Migrar `base.py:728` e `celery.py:22` para `init_sentry("backend")` / `init_sentry("worker")`, preservando o que hoje só existe inline: filtro de **Redis transiente** (backend) e garantindo o **scrubbing de breadcrumb** (que o worker ganha de brinde ao usar o helper).
3. Teste de guarda: afirmar que cada serviço inicializa com o conjunto de integrations esperado.

### e) Ressalvas
- Não perder o `_is_redis_transient_event` do backend ao consolidar — hoje ele só existe no init inline.

### f) Confiança: **Sei**.

---

## Item 6 — beforeSend / Inbound Filters: scanner, ruído de auth e filtro de health morto

**Onda 0 · Backend · Esforço M · Sem 2 · Status: Não iniciado**

### a) O que a etapa exige
Filtrar `DisallowedHost` (scanner de IP) via ALLOWED_HOSTS/Inbound Filter; **não** dropar auth em bloco (são incidentes reais — reclassificar por endpoint/causa); e **corrigir o caminho de health em dois filtros mortos** (`before_send` em `base.py:716` e middleware `api_logging.py:18`), pois o endpoint real é `/api/core/healthcheck/`.

### b) O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - `before_send` `base.py:713-723` casa `event...url.endswith("/health/")`. Middleware `api_logging.py:18` → `EXCLUDED_PATHS = {"/api/health/", "/health/"}`.
  - **Endpoint real = `/api/core/healthcheck/`**: `apps/core/urls.py:12` define `healthcheck/`, montado em `api/core/` por `config/urls_public.py:45` e `config/urls_tenant.py:76`. View trivial `apps/core/views.py:21` → `Response({"status": "ok"})`. Doc §3/§109 confirma o caminho e diz "**Não** existe rota `/health/`".
  - **Conclusão:** os dois filtros casam `/health/`, que **não existe** → **filtro morto**; e nenhum exclui `/healthcheck/`. Confirma o xlsx.
  - `DisallowedHost`: **sem tratamento dedicado para Sentry**; `ALLOWED_HOSTS` listado em `production.py:14-20` (e wildcard `*` em `development.py`). Não há Inbound Filter/`before_send` para `DisallowedHost`.
  - Tags de tenant: `api_logging.py:25-33` chama `set_tenant_context` (`tenant_id`/`schema_name`) — relevante ao item 9.
- **Documentação:** §3 e §7 confirmam (healthcheck real, `DisallowedHost` = scanner/ruído 127 ev, auth ~275 ev como falhas "esperadas" logadas como error).
- **Sentry:** snapshot — `DisallowedHost` (BACKEND-1A) 127 ev; auth ~275 ev. (Não re-medido ao vivo nesta rodada; números do snapshot/doc.)

### c) Veredito
**Não cumprida** (confere). Premissa do xlsx **confirmada**, incluindo o caminho `/api/core/healthcheck/` (o filtro atual nunca casa).

### d) Plano concreto
1. **Corrigir os filtros de health:** trocar `"/health/"` por `"/api/core/healthcheck/"` no `before_send` (`base.py:716`) e em `EXCLUDED_PATHS` (`api_logging.py:18`). (Cruza com item 20, que torna o healthcheck um readiness real.)
2. **`DisallowedHost`:** filtrar via **Inbound Filter** no painel Sentry (mais simples que código) e/ou ajustar `ALLOWED_HOSTS`. Remover o wildcard `*` de `development.py` se vazar para prod.
3. **Auth: NÃO dropar em bloco.** Reclassificar por endpoint/causa (a análise viva de 09/06 mostra incidentes reais — Ultracargo em `/api/token/`, trial JWT, convite, forgot-password). Dropar só o que for comprovadamente scanner/ruído.

### e) Ressalvas
- A reclassificação de auth depende de análise por endpoint (não é regra única) — é trabalho de triagem, não só um filtro.

### f) Confiança: **Sei** (caminho do health e filtros mortos confirmados na 3 fontes).

---

## Item 7 — Scrubbing de PII/LGPD no Frontend + Data Scrubber server-side

**Onda 0 · Frontend · Esforço M · Sem 2 · Status: Não iniciado**

### a) O que a etapa exige
Backend já tem `send_default_pii=False`. No frontend: `sendDefaultPii:true` nos 3 configs + `Sentry.setUser({email})` + Session Replay (10%/100% em erro) **sem masking** sobre telas de CNH/ASO/CPF. Pôr `sendDefaultPii:false`, masking/seletores de bloqueio no replay, e Advanced Data Scrubbing na UI.

### b) O que cada fonte mostrou
- **Código (CONFIRMADO):**
  - `sendDefaultPii: true` em `instrumentation-client.ts:21`, `sentry.server.config.ts:16`, `sentry.edge.config.ts:17`.
  - `Sentry.setUser({ id, email })` em `modules/auth/hooks/useAuth.tsx:175` (login) e `:388` (selectTenant); `setUser(null)` no logout `:224`.
  - Session Replay `replaysSessionSampleRate: 0.1` / `replaysOnErrorSampleRate: 1.0` (`instrumentation-client.ts:18-19`), **sem** `maskAllText`/`blockAllMedia`/seletores — usa defaults do SDK.
  - Backend **`send_default_pii` não setado → default `False`** (ok) — `base.py:728-736` não menciona PII.
  - Custos `AutoChecker_Custos/src/instrument.ts:12` → `sendDefaultPii: true`.
- **Documentação:** §8 confirma todo o achado (inclui `.env.example` expondo `NEXT_PUBLIC_JWT_SECRET`, CPF/CNPJ em texto puro no DB).
- **Sentry:** não há o que medir por API; é configuração de SDK + regras de scrubbing no painel.

### c) Veredito
**Não cumprida** (confere). Premissa **confirmada** integralmente.

### d) Plano concreto
1. Frontend: `sendDefaultPii:false` nos 3 configs; **masking do replay** (`maskAllText: true`, `blockAllMedia: true`, e seletores específicos nas telas de CNH/ASO/CPF). Confirmar **qual frontend** é o produtivo (ressalva global #2) e aplicar nos dois se ambos forem deployados.
2. Reavaliar `Sentry.setUser` para enviar só `id` (sem `email`) — ou anonimizar.
3. **Advanced Data Scrubbing** (server-side, painel Sentry) como rede de segurança: regras para CPF/CNPJ/e-mail.
4. Corrigir `sendDefaultPii:true` do Custos.
5. (Compliance, fora do escopo de obs.) avaliar criptografia de CPF/CNPJ em repouso — cruza com item 31.

### e) Ressalvas
- `default False` do backend é por convenção do `sentry-sdk` (não há linha explícita) — correto, mas frágil; vale fixar `send_default_pii=False` explicitamente ao consolidar o init (item 5).

### f) Confiança: **Sei**.

---

## Item 8 — Triagem ZERO do backlog (152 issues)

**Onda 0 · AutoChecker · Esforço M · Sem 2 · Status: Não iniciado**

### a) O que a etapa exige
Classificar todas as issues (Resolved / Ignored com prazo / In Progress), documentar critério, excluir o schema público dos alertas. Hoje **0 issues resolvidas em 30 dias**.

### b) O que cada fonte mostrou
- **Código:** nada a auditar — regras/alertas e status de issue **vivem só no painel Sentry** (busca por `alert`/`rule` no repo só achou componentes de UI). Confirmado.
- **Documentação:** §7 — "3 projetos · 152 issues · 0 resolvidas. Worker 94, backend 56, frontend 2."
- **Sentry ao vivo (12/06):**
  - `is:resolved` na org retorna **8 issues — todas do AutoLoad V4** (`AUTOLOADV4-EDGEGATEWAY-*`). **Nenhuma do AutoChecker.** → a afirmação "0 resolvidas no AutoChecker" **continua verdadeira hoje**.
  - Backlog do worker segue cheio e ativo (top por frequência): `WORKER-9 Task failed` **689 ev** (visto há 29 min — subindo, bate com a sessão de hoje no FollowUp), `WORKER-1G relation…notificationlog` 544, `WORKER-5 site check` 314, `WORKER-N/K relatório/preferência` 241/242, `WORKER-2/1 Firebase/FCM` 171/169, `WORKER-1R/1Q webhook 404` 135/135.

### c) Veredito
**Não cumprida** (confere). A triagem **não começou**: 0 resolvidas no AutoChecker até hoje.

### d) Plano concreto
1. Definir **critério escrito** de triagem (quando Resolve / Ignore-com-prazo / In Progress) e dono por projeto.
2. Passar issue a issue (começar pelos top ofensores, que cruzam com itens 3/4/15/22/27/28): resolver as já corrigidas, **Ignore com prazo** o ruído (UNAVAILABLE, auth esperada), atribuir o resto.
3. **Excluir o schema `public`** dos alertas/queries (cruza item 4 e 18).
4. Meta: backlog com dono e tendência de "resolved/30d" > 0.

### e) Ressalvas
- O total "152 issues" é do snapshot 04/05→03/06; o número exato de issues abertas **hoje** não foi recontado por API nesta rodada (o MCP lista issues, não devolve um total agregado simples). O que **foi** confirmado ao vivo é o fato crítico: **0 resolvidas no AutoChecker**.

### f) Confiança: **Sei** (o ponto central — 0 resolvidas — confirmado ao vivo; o total exato de hoje fica **Parcial**).

---

## Tabela-resumo — Onda 0

| # | Etapa | Status cronograma | Veredito (situação real) | Confiança | Esforço p/ resolver |
|---|---|---|---|---|---|
| 1 | environment nos 3 SDKs + isolar DEV/PRD | Concluído | **Parcial** — código pronto; isolamento depende do deploy/KPI | Parcial | M |
| 2 | Release `<comp>@<hash>` + set-commits | Em andamento | ➡ ver `Etapa2_*.md` | — | M |
| 3 | PeriodicTask órfã do Beat | Pendente | ➡ ver `Etapa3_*.md` (órfã provável em `/tmp/celerybeat-schedule`) | — | P |
| 4 | migrate_schemas + gate de drift | Não iniciado | **Não cumprida** — confirmada na 3 fontes (ao vivo: WORKER-1G 544 ev) | Sei | M |
| 5 | Consolidar init no `init_sentry` | Não iniciado | **Não cumprida** — helper nunca chamado; precisa alterar o helper | Sei | P |
| 6 | beforeSend / filtros / health morto | Não iniciado | **Não cumprida** — filtros casam `/health/`, real é `/api/core/healthcheck/` | Sei | M |
| 7 | PII/LGPD no Frontend | Não iniciado | **Não cumprida** — `sendDefaultPii:true`×3 + setUser(email) + replay sem mask | Sei | M |
| 8 | Triagem ZERO do backlog | Não iniciado | **Não cumprida** — 0 resolvidas no AutoChecker (confirmado ao vivo) | Sei (total: Parcial) | M |

### O que ficou marcado como Parcial / Não sei
- **Item 1:** distribuição de `environment` do frontend ("15% production") **não reproduzida** ao vivo via MCP (errors/30d ≠ all-events da janela do snapshot).
- **Item 8:** total exato de issues abertas **hoje** não recontado por API (o fato "0 resolvidas" foi confirmado).
- **Global:** qual dos **dois frontends** é o produtivo — **a confirmar com o time** (impacta itens 1, 7).
- **Global:** o doc `Auditoria_Cronograma_vs_Codigo_AutoChecker_2026-06-10` citado no xlsx **não existe** nos repositórios.

---

> **Checkpoint:** esta entrega cobre **apenas a Onda 0** (o GATE). As Ondas 1–6 (itens 9–31) ficam para a próxima rodada, conforme o princípio do plano ("sanear antes de ampliar").
