# Documentação Técnica — AutoChecker

> **Base:** análise estática do código real em `C:\Autochecker` (03/06/2026).
> **Organização Sentry:** `automind-qd` — projetos `autochecker-backend`, `autochecker-worker`, `autochecker-frontend`.
> **Propósito:** documentar a arquitetura real e o estado de observabilidade do AutoChecker, servindo de base para o cronograma de observabilidade e a triagem de incidentes.

---

## 1. Visão geral

Plataforma **SaaS multi-tenant de validação documental e compliance** para transporte e logística no Brasil (RegTech: ANTT, SERPRO, RNTRC, MOPP, INMETRO, IBAMA). Centraliza o ciclo de vida dos documentos de motoristas e veículos: **upload → OCR → classificação → extração → autenticação → integração**.

O produto **não é um único repositório**. Em `C:\Autochecker` há **7 diretórios** que compõem o ecossistema:

| Diretório | O que é | Stack | Projeto Sentry |
|---|---|---|---|
| `AutoChecker` | Monorepo principal: **backend** (Django/DRF) + **worker** (Celery) + **shared** + **frontend** (Next.js) + **autochecker-scraping-server** (Selenium) | Python 3.11 / Node 20 | backend, worker, frontend |
| `AutoChecker_Frontend` | Frontend web do cliente (cópia/repo dedicado do Next.js) | Next.js 14 | `autochecker-frontend` |
| `AutoChecker_OCR` | Microserviço HTTP de OCR (AWS Textract) | FastAPI + Flask | **nenhum** |
| `Scrapping` | Serviço de scraping de sites governamentais (Selenium/EC2) | *(código não disponível localmente — só README)* | **a confirmar** |
| `AutoChecker_AIAgent` | Ingestão de documentos por **WhatsApp** + agente de IA | FastAPI + Celery + Evolution API | **nenhum** |
| `AutoChecker_APP` | App mobile/web do cliente (scaffold inicial) | Expo / React Native 0.79 | **nenhum** |
| `AutoChecker_Custos` | Monitor de custos de nuvem (AWS/DO/Brevo/OpenAI) | NestJS 11 | **nenhum dedicado** (DSN ambíguo) |

> **Achado de cobertura:** apenas backend, worker e frontend reportam ao Sentry. OCR, AIAgent e APP **não têm Sentry**; Custos tem `@sentry/nestjs` no código mas **sem projeto dedicado** na org (`automind-custos` não existe). Ver §8.

---

## 2. Monorepo principal (`AutoChecker/`)

Estrutura real:

```
AutoChecker/
├── backend/                  # Django 4.2 + DRF (API HTTP)
│   ├── apps/                 # accounts, audit, authentication, composition, core,
│   │                         #   integrations, metrics, mobile, notifications,
│   │                         #   portal, tenants, trial, upload, utils, validation
│   ├── config/
│   │   ├── settings/         # base.py, development.py, production.py, testing.py,
│   │   │                     #   celery_settings.py
│   │   ├── middleware/       # api_logging.py, rate_limit_monitor.py, ...
│   │   ├── celery.py, urls.py, urls_public.py, urls_tenant.py, firebase/
│   ├── requirements.txt, pyproject.toml, manage.py
├── worker/                   # Celery worker dedicado (settings Django próprio)
│   ├── apps/validation/tasks/  # entry, ocr, classification, extract, authenticator,
│   │                           #   recalculate, reprocess, schedule_reprocess,
│   │                           #   site_monitoring; + extractors/ e auth_providers/
│   ├── config/               # celery.py, celery_logging.py, settings/
│   ├── promtail-config-{dev,prod}.yml, docker-compose.{dev,prod}.yml, redis.conf
├── shared/                   # pacote comum aos dois serviços
│   ├── observability/        # sentry.py  ← helper init_sentry (NÃO usado por ninguém)
│   ├── services/             # composition.py, integration_dispatch.py, ... (15 módulos)
│   ├── tasks/                # integration_tasks, notification_tasks, report_tasks
│   ├── integrations/         # generic_provider.py, template_engine.py
│   ├── adapters/             # email (Brevo), whatsapp (360Dialog), push (Firebase)
│   ├── models/, utils/, tests/
├── frontend/                 # Next.js (Sentry próprio)
├── autochecker-scraping-server/   # servidores Selenium v1/v2 (autenticação de documentos)
├── ocr/, check_sites/, docs/
```

### 2.1 Stack & versões (de `requirements.txt`)

- **Backend:** `Django==4.2.10`, `djangorestframework==3.14.0`, `djangorestframework-simplejwt==5.3.1`, `drf-spectacular`.
- **Worker:** `celery==5.3.6`, `redis==5.0.1` (broker `redis://redis:6379/0`, result backend `/1`), `django-celery-beat==2.5.0`.
- **Multi-tenancy:** `django-tenants==3.5.0`.
- **Observabilidade:** `sentry-sdk==1.40.5`; logs JSON → Promtail → Grafana Loki.
- **Externos:** `boto3==1.34.69` (Textract/S3), `openai==1.83.0` (worker), Firebase, 360Dialog, Brevo.
- **Segurança (instalados):** `django-axes==6.3.0`, `django-csp==3.7`, `django-ratelimit==4.1.0`, `django-storages==1.14.2`, `django-health-check==3.17.0`.

### 2.2 Multi-tenancy

`django-tenants` com **um schema PostgreSQL por tenant**. `SchemaHeaderMiddleware` resolve o schema por requisição (headers `X-Tenant-ID`/`X-Schema-Name` ou claim `schema_name` do JWT). `SHARED_APPS` no schema `public` (tenants, portal, accounts, audit, metrics); `TENANT_APPS` por tenant (core, upload, validation, composition, notifications, mobile). Planos BASIC/ENTERPRISE; módulos habilitáveis por tenant.

> ⚠️ **Risco operacional (confirmado):** o deploy roda `migrate`/`migrate --plan` (`backend/scripts/deploy.sh:97`, `backend.azure-pipelines.yml:148`), **nunca `migrate_schemas`**. Em django-tenants, `migrate` não aplica migrações aos schemas de tenant → erros `relation "..." does not exist` em runtime (ver §7). `migrate_schemas` só aparece em `reset_db_django.py:126`. **Não há gate de migração por schema no deploy.**

### 2.3 Pipeline de documentos (worker)

6 estágios encadeados via `transaction.on_commit()` + `.apply_async()` (encadeamento explícito):

1. **Entry** (`validation_entry`) — valida MIME, SHA256/dedup, S3 dual-bucket AES256, cria `Document`.
2. **OCR** (`ocr_heavy`) — AWS **Textract** (`boto3.client("textract")`).
3. **Classificação** (`ai_processing`) — OpenAI **gpt-4o-mini** (`classification.py`).
4. **Extração** (`data_processing`) — extractors especializados em `worker/apps/validation/tasks/extractors/`.
5. **Autenticação** (`auth_selenium`) — via **servidores Selenium** (`autochecker-scraping-server/`, v1/v2) para CNH/CRLV/CIV/CIPP/CTPP/CVV/Cronotacógrafo/CR/MR. (Não é um provider OAuth2 SERPRO genérico — a autenticação é por scraping.)
6. **Integração** (`integrations`) — dispatch para sistemas externos do tenant.

**17 tipos de documento** em `Document.TYPE_CHOICES` (`shared/models/upload.py:324-342`).

**11 filas Celery** (`config/settings/celery_settings.py` — `CELERY_TASK_ROUTES`): `validation_entry`, `ocr_heavy`, `ai_processing`, `data_processing`, `auth_selenium`, `admin_tasks`, `monitoring`, `notifications`, `notifications_retry`, `reports`, `integrations`.

**Limites de task (confirmado):** definidos via `CELERY_TASK_ANNOTATIONS` (`celery_settings.py:108-122`) — textract `time_limit=600`/`soft=480`; authenticate `900`/`720` — e limite global `CELERY_TASK_TIME_LIMIT=1200`. (Não estão no decorator `@shared_task`, e sim nas annotations.)

> ⚠️ **Divergência de beat schedule:** `worker/config/celery.py:69` define **8** jobs (efetivo) e `worker/config/settings/celery_settings.py:31` define **6** para a mesma propriedade — risco de jobs fantasma conforme qual settings carrega.

### 2.4 Integrações & notificações

- **Framework de integração DB-driven** (`shared/integrations/generic_provider.py`): tipos de auth incl. `oauth2_client_credentials` (`_obtain_oauth2_token`, grant_type client_credentials); template engine própria.
- **Notificações multicanal** (`shared/adapters/`): Email (Brevo), WhatsApp (**360Dialog**, `waba-v2.360dialog.io`), Push (**Firebase FCM**, `shared/adapters/push.py`). Retry com backoff.
- **OCR:** AWS Textract; **Classificação:** OpenAI gpt-4o-mini.

---

## 3. Backend (`AutoChecker/backend`)

Django 4.2 + DRF, multi-tenant. ~167 endpoints OpenAPI (drf-spectacular). Apps de domínio em `backend/apps/`.

- **Healthcheck:** `django-health-check` exposto em **`/api/core/healthcheck/`** (`apps/core/urls.py:12`, `urls_tenant.py:76`). **Não** existe rota `/health/`.
- **Middleware de log:** `config/middleware/api_logging.py` — seta contexto de tenant (`set_tenant_context`, tags `tenant_id`/`schema_name`, `:28-33`) e é o **único** ponto com `capture_exception` (`:40`). Mascara chaves sensíveis (`cpf|cnpj|password|token|secret`).

---

## 4. Frontend (`AutoChecker_Frontend` e `AutoChecker/frontend`)

Next.js **14** (Pages Router), React 18, TypeScript 5.8, Tailwind 3 + shadcn/ui, Zustand, React Query 5, Recharts. SDK Sentry **`@sentry/nextjs ^10.43.0`**.

Sentry inicializado em `instrumentation-client.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts` (+ `instrumentation.ts` com `onRequestError`). `next.config.js` usa `withSentryConfig`.

Config relevante (client):
```ts
environment: process.env.NEXT_PUBLIC_SENTRY_ENVIRONMENT || "development",
integrations: [Sentry.replayIntegration()],
tracesSampleRate: env === "production" ? 0.2 : 1.0,
replaysSessionSampleRate: 0.1,
replaysOnErrorSampleRate: 1.0,
sendDefaultPii: true,   // ← nos 3 configs
```

> ⚠️ Ver §8 (privacidade) — `sendDefaultPii: true` + `Sentry.setUser({id,email})` + Session Replay sem masking explícito. `release`/`org`/`project` com defaults de teste (`automind-teste`/`javascript-nextjs`).

---

## 5. Serviços auxiliares

- **`AutoChecker_OCR`** — microserviço FastAPI (+ Flask para ORM) sobre **AWS Textract** (region default `us-east-2`). Endpoints `/ocr/*` e `/health` (raso — não checa dependências). **Sem Sentry.** Polling de jobs Textract em `while True` **sem timeout**. Backoff fixo `sleep(5–20s)` em toda chamada. OpenAI gpt-4o-mini só para INEMA (usa API legada `ChatCompletion`, quebra com openai 1.x → cai em fallback regex). Não calcula `Confidence`/qualidade.
- **`Scrapping`** — repo Azure DevOps; **código não presente localmente** (só README). Provável origem da autenticação por Selenium em EC2 e da checagem de disponibilidade de sites. *A issue Sentry `Error checking site http://ec2-...` (worker) está em `worker/apps/validation/tasks/site_monitoring.py` + `check_sites/`, não no OCR.*
- **`AutoChecker_AIAgent`** — stack Docker Compose: Evolution API (WhatsApp/Baileys) + agente FastAPI + **Celery worker próprio** + Redis. LangChain + OpenAI. Faz upload de docs ao backend. **Sem Sentry** — o Celery worker daqui **não é** o `autochecker-worker` e está fora do radar.
- **`AutoChecker_APP`** — Expo SDK 53 / React Native 0.79 / React 19, expo-router. Scaffold inicial (camada de dados mock). **Sem Sentry** (`@sentry/react-native` ausente). **Não há push implementado** (notificações são mock) → as issues APNs/FCM **não vêm daqui** (vêm do `shared/adapters/push.py` no backend/worker).
- **`AutoChecker_Custos`** — NestJS 11 monitor de custos (AWS Cost Explorer, DO, Brevo, OpenAI). **Tem `@sentry/nestjs`** (`instrument.ts`, `SentryGlobalFilter`), mas: (a) **sem projeto Sentry dedicado**; (b) bug — código lê `SENTRY_DSN` e o `CLAUDE.md:98` documenta `SENTRY_DNS` (typo) → se seguir a doc, Sentry inicia silenciosamente sem enviar nada.

---

## 6. Observabilidade atual — resumo

| Aspecto | Estado real |
|---|---|
| Sentry backend | `sentry_sdk.init` **direto** em `settings/base.py:728` — integrations `[DjangoIntegration, RedisIntegration]` (**sem Celery**). Filtro anti-ruído Redis (`_is_redis_transient_event`). `traces_sample_rate` lido de env (default 0.2). |
| Sentry worker | `sentry_sdk.init` **direto** em `config/celery.py:22` — `[DjangoIntegration, CeleryIntegration, RedisIntegration]`. `before_send` = lambda que só filtra `/health/`. |
| Helper `init_sentry` | Existe em `shared/observability/sentry.py` (adicionaria CeleryIntegration ao worker) mas **não é chamado por ninguém** → config duplicada e drift. |
| Captura de domínio | Fora do middleware HTTP, **nenhum** `try/except` de negócio chama `capture_exception`. Centenas de `logger.error/exception` (composição, webhooks, notificações, tenants, classificação) só vão para Loki. |
| Tags | `tenant_id`/`schema_name` por request e por task (positivo). |
| Logs | JSON → Promtail → Loki (`monitor.autochecker.cloud`). |
| Alertas Sentry | Apenas 1 regra default ("high priority issues"), **sem filtro de ambiente** (`env=None`). |

---

## 7. Retrato do Sentry (snapshot 04/05→03/06/2026)

3 projetos · **152 issues · 0 resolvidas**. Worker 94 issues, backend 56, frontend 2. Por volume de eventos (events-stats): backend ~296k, frontend ~122k, worker ~11k/30d.

Issues dominantes e causa real:

| Issue | Eventos | Causa raiz (código real) |
|---|---|---|
| `KeyError: ...process_scheduled_notifications` (BACKEND-1H/WORKER-1F) | ~1.640 | Task **comentada** (`worker/apps/notifications/tasks/notification_tasks.py:50`) e fora de todo beat_schedule do código → **`PeriodicTask` órfã no DB** (django-celery-beat) ainda a agenda → KeyError no dispatch. |
| `relation "..." does not exist` (WORKER-1G/M/R/P/Q/V/1D) | ~1.267 (57 issues) | **Migrações não aplicadas em schemas de tenant** — deploy roda `migrate`, nunca `migrate_schemas` (§2.2). |
| `Task failed` (WORKER-9) | 614 | Captura genérica sem fingerprint/contexto. |
| `Error checking site http://ec2-...` (WORKER-5) | 297 | Checagem de disponibilidade de site (`worker/.../site_monitoring.py`) — `UNAVAILABLE` (esperado) logado como `error`. |
| `Erro na geração do relatório <uuid>` / `Preferência <uuid> não encontrada` | ~192 | Alta cardinalidade (UUID no título) → fragmentação de grouping. |
| Notificação/Webhook/Firebase (NotRegistered, APNs, HTTP 404) | ~368 (29 issues) | `shared/adapters/push.py` + webhooks de integração; falhas permanentes não distinguidas. |
| `SchemaHeaderMiddleware`/`TenantJWTAuthentication` | ~275 | Falhas esperadas de auth/tenant logadas como `error`. |
| `DisallowedHost` (BACKEND-1A) | 127 | Scanner de IP — ruído a filtrar por Inbound Filter. |
| `Cannot connect to redis://127.0.0.1:6379` (BACKEND-W) | 111 | Config de ambiente apontando para localhost. |
| `N+1 Query` (BACKEND-5) | 122 | Performance — visível porque tracing está ativo. |

**Tagging de environment:** backend 96% production ✅, **frontend só 15%** (NEXT_PUBLIC_SENTRY_ENVIRONMENT com fallback `development` — DEV poluindo prod), worker 65%.

---

## 8. Segurança & privacidade (achados confirmados)

- **CORS:** `CORS_ALLOW_ALL_ORIGINS = True` em produção (`production.py:34`).
- **PII em texto puro:** CPF/CNPJ como `CharField` sem cripto (`shared/models/accounts.py`, `upload.py`, `tenants.py`).
- **`django-csp` / `django-axes`:** instalados em `requirements` mas **ausentes** de `INSTALLED_APPS`/`MIDDLEWARE` → inativos.
- **Frontend / LGPD:** `sendDefaultPii: true` (envia IP/headers/cookies/body) + `Sentry.setUser({email})` + Session Replay (10% sessões, 100% em erro) **sem masking explícito** sobre telas que exibem CNH/ASO/CPF. `.env.example` expõe `NEXT_PUBLIC_JWT_SECRET` (segredo no client).
- **OCR:** `.env.example` com senha real de Postgres; CORS `*` com `allow_credentials=True`.
- **AIAgent / Custos:** chaves default fracas em `.env.example`; `sendDefaultPii: true` no Custos.

---

## 9. Fontes

- Análise estática do código em `C:\Autochecker` (backend/worker/shared, frontend, OCR, AIAgent, APP, Custos), 03/06/2026.
- Snapshot ao vivo da API Sentry (`automind-qd`), janela 04/05→03/06/2026, 3 projetos AutoChecker.
- `Estudo de melhoria de observabilidade/Oportunidades de Melhoria de Observabilidade - AutoChecker.md` (14/04/2026).
