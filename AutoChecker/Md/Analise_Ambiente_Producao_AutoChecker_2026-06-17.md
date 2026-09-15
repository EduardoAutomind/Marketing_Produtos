# Análise do ambiente `production` — AutoChecker

> Views, funções, páginas e jobs mais utilizados em produção, com performance, erros, base de usuários e contexto.

| | |
|---|---|
| **Data** | 17/06/2026 |
| **Produto** | AutoChecker (backend Django/Python · frontend Next.js · worker Celery · multi-tenant por schema) |
| **Org Sentry** | `automind-qd` |
| **Ambiente** | `production` |
| **Janela** | Últimos 30 dias |
| **Fonte** | Dados ao vivo do Sentry (`spans` e `errors`), projetos `autochecker-frontend`, `autochecker-backend`, `autochecker-worker` |

---

## ✅ Premissa: instrumentação completa (o oposto do AutoLoad)

Diferente do AutoLoad (onde só o frontend reporta em prod), o **AutoChecker tem a stack inteira instrumentada em produção** e ambientes **limpos** (`production` + `staging`, sem rótulos duplicados):

| Projeto | Transações `production` (30d) | Tem telemetria prod? |
|---|---:|:---:|
| `autochecker-backend` | 98.967 | ✅ |
| `autochecker-frontend` | 61.970 | ✅ |
| `autochecker-worker` | 10.004 | ✅ |

Isso permite ver **diretamente** as views de API (Django), as telas (Next.js) e os jobs (Celery) — sem reconstrução indireta. É a referência de observabilidade entre os produtos.

---

## 📊 1. Retrato do ambiente `production`

| Métrica | Valor |
|---|---|
| Transações backend (30d) | **98.967** |
| Transações frontend (30d) | **61.970** |
| Transações worker (30d) | **10.004** |
| Usuários únicos (frontend) | **980** |
| Domínio | `autochecker.cloud` (worker auxiliar em `aux-server.autochecker.cloud`) |
| Arquitetura | Multi-tenant por **schema** (Django + middleware `SchemaHeaderMiddleware` / `TenantJWTAuthentication`) |
| Tempo real / notificações | Polling de inbox + Firebase Cloud Messaging (push) + WhatsApp |

---

## 🖥️ 2. Telas mais usadas — frontend (Next.js)

Páginas reais (client-side), com a latência percebida pelo usuário:

| # | Tela | Acessos | p75 | p95 |
|---|------|--------:|----:|----:|
| 1 | **Configurações do tenant** `/tenant/settings` | 938 | 1,11 s | 2,09 s |
| 2 | **Documentos** `/tenant/documents` | 709 | 🔴 2,04 s | 🔴 3,40 s |
| 3 | **Login** `/login` | 526 | 1,57 s | 3,14 s |
| 4 | **Home do tenant** `/tenant/home` | 364 | 1,81 s | 🔴 4,19 s |
| 5 | **Upload** `/tenant/upload` | 252 | 1,23 s | 2,67 s |

**Leitura:** o fluxo gira em torno de **Documentos** (lista, upload, visualização) — é o core do produto (validação documental). As telas-chave têm p95 de 3–4 s, sinalizando espaço de otimização.

### BFF / rotas de API do frontend mais chamadas

| Rota (Next.js BFF) | Chamadas | p95 |
|---|--------:|----:|
| `GET /api/notifications/inbox-get-unread` | 25.820 | 562 ms |
| `GET /api/permission/get` | 5.825 | 572 ms |
| `GET /api/trial/status` | 2.600 | 358 ms |
| `GET /api/login/companySwitch` | 2.385 | 915 ms |
| `GET /api/notifications/inbox-list` | 2.270 | 679 ms |
| `GET /api/document/list-paged` | 1.180 | 1,64 s |
| `GET /api/document/view` | 535 | 2,57 s |

---

## 🔌 3. Views de backend (Django) mais usadas em produção

| # | View / endpoint | Chamadas | p75 | p95 |
|---|---|--------:|----:|----:|
| 1 | `/api/notifications/inbox/unread_count/` | 25.835 | 113 ms | 302 ms |
| 2 | `/api/core/permissions/` | 5.890 | 129 ms | 334 ms |
| 3 | `/` (root/health) | 4.955 | 4 ms | 7 ms |
| 4 | `/api/trial/status/` | 2.660 | 121 ms | 259 ms |
| 5 | `/api/tenants/all-tenants-switcher/` | 2.375 | 🔴 402 ms | 🔴 831 ms |
| 6 | `/api/notifications/inbox/` | 2.300 | 128 ms | 245 ms |
| 7 | `/api/documents/upload-usage/` | 1.545 | 139 ms | 295 ms |
| 8 | `/api/documents/` | 1.270 | 531 ms | 1,04 s |
| 9 | `/api/accounts/me/` | 915 | 106 ms | 256 ms |
| 10 | `/api/validation/site-monitoring/` | 555 | 149 ms | 310 ms |
| 11 | `/api/documents/processed/` | 555 | 162 ms | 359 ms |
| 12 | `/api/documents/{document_id}/view/` | 535 | 379 ms | 668 ms |
| 13 | `/api/accounts/users/all_users/` | 405 | 128 ms | 199 ms |
| 14 | `/api/accounts/groups/all-groups/` | 400 | 161 ms | 257 ms |
| 15 | `/api/accounts/login/step1/` | 385 | 🔴 809 ms | 1,22 s |
| — | `/api/entity/driver/` · `/api/entity/vehicle/` | 320 · 235 | ~120 ms | ~200 ms |
| — | `/api/integrations/providers/` | 245 | 106 ms | 318 ms |

**Insight #1 — polling domina tudo.** `inbox/unread_count/` (backend 25.835 + BFF 25.820 ≈ **52 mil chamadas**) é ~⅓ de todo o tráfego. Maior alavanca de otimização: trocar polling por push/websocket ou aumentar o intervalo.

### 🤖 Ruído de varredura de segurança (bots)

O backend recebe scans automáticos procurando segredos/PHP — respondem rápido (404), mas poluem os dados e indicam exposição:

| Alvo | Hits |
|---|---:|
| `/.env` · `/.env.local` · `/.env.production` | 1.180 · 235 · 230 |
| `/index.php` | 210 |
| `/favicon.ico` · `/*` | 355 · 460 |

> Recomendado: bloquear esses padrões no edge (Cloudflare/WAF) e filtrar (`inbound filter`) no Sentry para não contar como transações.

---

## ⚙️ 4. Jobs do worker (Celery) mais executados

| # | Task | Execuções | p75 | p95 |
|---|---|--------:|----:|----:|
| 1 | `report_tasks.generate_user_scheduled_report` | 4.318 | 480 ms | 2,05 s |
| 2 | `notification_tasks.process_notification_task` | 2.291 | 911 ms | 1,17 s |
| 3 | `integration_tasks.integration_reauth` | 1.776 | 551 ms | 928 ms |
| 4 | `validation.tasks.classification.classify_document` | 270 | 2,93 s | 4,03 s |
| 5 | `validation.tasks.authenticator.authenticate_document` | 265 | 🔴 **61,9 s** | 🔴 **63,6 s** |
| 6 | `validation.tasks.entry.process_document_validation` | 190 | 135 ms | 180 ms |
| 7 | `validation.tasks.extract.extract_data` | 167 | 🔴 8,2 s | 9,2 s |
| 8 | `validation.tasks.ocr.run_textract` | 160 | 🔴 30,5 s | 🔴 52,6 s |
| 9 | `report_tasks.generate_scheduled_reports` | 152 | 1,42 s | 3,17 s |
| 10 | `validation.tasks.site_monitoring.collect_sites_availability` | 143 | 🔴 21,2 s | 24,6 s |

**Insight #2 — pipeline de validação documental é o peso.** OCR (`run_textract` 30–52 s), `authenticate_document` (**62 s**), `extract_data` (8 s) e `collect_sites_availability` (21 s) são os mais lentos. São assíncronos (tolerável), mas `authenticate_document` a 62 s p75 merece investigação de timeout/dependência externa.

---

## 🐛 5. Erros em produção

### Backend (Django)

| Erro | Eventos | Avaliação |
|---|----:|---|
| `KeyError: 'shared.tasks.notification_tasks.process_scheduled_notifications'` | 243 | 🔴 **Task órfã no Celery Beat** — agenda aponta p/ task removida/renomeada (ver Etapa 3) |
| `[TenantJWTAuthentication] Autenticação JWT falhou` (vários endpoints públicos) | 179+105+27+24+23… | ⚠️ Em endpoints públicos é esperado, mas logado como **erro** = ruído (deveria ser warning) |
| `[SchemaHeaderMiddleware] Erro ao processar token JWT` | 45 | Auth/token |
| `DisallowedHost: '192.0.2.1' / '159.223.151.055'` | 43+13 | 🔍 Scan/probe — ruído de segurança |
| `FieldError: Cannot resolve keyword 'name'` | 19 | 🔴 **Bug de query** real |
| `SchemaHeaderMiddleware: Tenant não encontrado` (autochecker, basecompartilhada) | 21+19 | Resolução multi-tenant |
| `consumer: Cannot connect to redis://10.116.0.6:6389` | 13 | Blip de infra (Redis) |

> `count_unique(user)` = 0 em todos — erros server-side não carregam contexto de usuário. Enriquecer com user/tenant ajudaria no diagnóstico.

### Worker (Celery)

| Erro | Eventos | Avaliação |
|---|----:|---|
| `Task failed` (genérico) | 159 | Falta de mensagem específica |
| `Erro HTTP ao enviar webhook: 404 - Token "…" not found` | 153 | 🔴 Entrega de **webhook** quebrada (token inválido) |
| `ProgrammingError: relation "notifications_notificationlog" does not exist` | 87 | 🔴 **Migração não aplicada** em schema de tenant |
| `ProgrammingError: relation "upload_document" does not exist` | 34 | 🔴 Idem — tabela ausente em schema |
| `RuntimeError: Falha no scraping certificado CIV/CIPP … Retentar (Erro exótico)` | 29+17+16+14+12… (>100) | Dependência externa (scraping gov) instável |
| `KeyError: '…process_scheduled_notifications'` | 23 | 🔴 Mesma task órfã do Beat (também no worker) |
| `Erro HTTP ao enviar WhatsApp: 404 - Template 'password_reset' não existe` | 18+12 | 🔴 **Reset de senha por WhatsApp quebrado** |
| `Error checking site aux-server.autochecker.cloud: ReadTimeout` | 13 | Timeout no monitor de sites |

### Frontend (Next.js) — muito limpo

| Erro | Eventos | Usuários | Avaliação |
|---|----:|----:|---|
| `FirebaseError: Messaging unsupported-browser` | 26 | 16 | Ruído (compat de navegador p/ push) |
| `t.with` | 2 | 2 | Minificado (faltam source maps?) |
| `Object Not Found Matching Id… MethodName:update` | 1 | 1 | Ruído WebSocket |

---

## 💡 6. Síntese e recomendações

1. **Reduzir polling de notificações.** `inbox/unread_count/` é ~⅓ do tráfego (52k req). Migrar para push (já há FCM) / websocket, ou aumentar intervalo — maior alavanca de custo/performance.
2. **Corrigir a task órfã do Beat** (`process_scheduled_notifications`, 243+23 erros). Já mapeada na **Etapa 3** do cronograma (tickets #53659/#53707). Item de fechamento rápido.
3. **Migrações faltando em schemas de tenant** (`notifications_notificationlog`, `upload_document`). Risco real de perda de notificação/documento para alguns tenants — auditar `migrate_schemas`.
4. **WhatsApp `password_reset` template ausente** — reset de senha por WhatsApp falhando. Cadastrar/aprovar template na Meta.
5. **Performance do pipeline documental.** `authenticate_document` 62 s e `run_textract` 30–52 s — revisar timeouts e dependências externas.
6. **Reduzir ruído no Sentry:** rebaixar `TenantJWTAuthentication` em endpoints públicos para warning; filtrar scans (`/.env`, `DisallowedHost`) no edge + inbound filters. Limpa o sinal real.
7. **Telas lentas:** `/tenant/documents` (p95 3,4 s) e `/tenant/home` (p95 4,2 s) — investigar (provável `documents/list-paged` p95 1,6 s + payload).

---

## Anexo — Notas de método

- Contagens do dataset `spans` (transações e jobs) e `errors`, filtradas por `environment:production`, janela 30 dias.
- Latências `p75`/`p95` em `span.duration`.
- "Usuários únicos" = `count_unique(user)` (só frontend tem contexto de usuário; backend/worker = 0).
- Consulta feita **projeto a projeto** (agregados org-wide do MCP vêm truncados).

*Documento gerado em 17/06/2026 a partir de dados ao vivo do Sentry.*
