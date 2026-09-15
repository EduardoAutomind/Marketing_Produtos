# Mudanças no código do AutoChecker relevantes para Observabilidade

**Produto:** AutoChecker
**Fonte:** Azure DevOps — org `automindautomacao`, projeto `AutoChecker` (6 repositórios)
**Janela analisada:** 08/06/2026 → 30/06/2026
**Data da análise:** 30/06/2026
**Método:** varredura de commits/PRs nos 6 repos + leitura dos diffs dos PRs relevantes (`apps/integrations/views.py`, `shared/tasks/integration_tasks.py`, componentes de timeline do frontend) e do modelo/serializer `IntegrationLog`.

---

## TL;DR

Sim, houve **uma mudança grande e diretamente relevante**: o subsistema de **`IntegrationLog`** ganhou observabilidade *in-app* (timeline por entidade + retry manual), surfaceada na UI. É a primeira camada de observabilidade do AutoChecker que **não depende do Sentry**. Bom para o roadmap — mas acende um **alerta LGPD** (auditado em separado: `Auditoria_LGPD_IntegrationLog_AutoChecker_2026-06-30.md`), porque passa a **persistir e exibir payloads completos** que contêm PII.

**Não houve** nenhuma mudança de Sentry/DSN/instrumentação de erro no período.

---

## Repos com movimento no período

| Repositório | Commits no período | Relevante p/ observabilidade? |
|---|---|---|
| `AutoChecker` (backend Django) | sim | ✅ Sim — IntegrationLog |
| `AutoChecker_Frontend` (Next.js) | sim | ✅ Sim — IntegrationTimeline |
| `AutoChecker_APP` (mobile) | sim | ⚪ Não (LGPD/UX) |
| `AutoChecker_OCR` | — | sem commits |
| `AutoChecker_AIAgent` | — | sem commits |
| `AutoChecker_Custos` | — | sem commits |
| `Scrapping` | — | sem commits |

---

## 1. ⭐ Observabilidade in-app de integrações — PRs 15213 (backend) + 15214 (frontend), 29/06

Work item **#55909** (branch `fix/55909`).

### Backend — `backend/apps/integrations/views.py` (PR 15213)
- O `IntegrationLogViewSet` (ReadOnly, paginado 20/pág, `IntegrationsAccessPermission`) passou a **filtrar por `entity_type` e `entity_id`** — além dos filtros já existentes `status`, `event_type`, `provider_id`. Na prática: dá para puxar **o histórico/linha do tempo de integração de um motorista ou veículo específico**.
- Ganhou a ação **`retry`** (`POST .../retry`): re-despacha um log com `status="failed"` reenfileirando a task Celery `process_integration_event.delay(...)`, reaproveitando `log.request_payload`, `event_type`, `entity_id`, `entity_type`, `approved`. Só aceita logs `failed`; erros são logados com `logger.error(..., exc_info=True)`.
- Cobertura de testes adicionada (`test_integrations_views.py`): valida os filtros por entidade e a configuração read-only do viewset.

### Backend — `shared/tasks/integration_tasks.py`
- Cada evento de integração cria **um `IntegrationLog` por endpoint executado** (`_create_log` / `_update_log`), persistindo `request_payload` (entity_data), `endpoint_name`, `curl_command`, `request_body`, `status` (success/failed), `error_message`, `response_status_code`.
- Logging estruturado consistente com prefixos `[IntegrationTask]` / `[BatchDispatch]` (`logger.info`/`logger.error`).
- `BatchDispatchView` despacha motoristas/veículos em lote com contagem de `queued`/`skipped` e `skipped_reasons` — bom para diagnóstico operacional.

### Frontend — `AutoChecker_Frontend` (PR 15214)
- Novos componentes: `IntegrationTimeline.tsx`, `IntegrationTimelineModal.tsx`, integrados às tabelas `DriversEntityTable.tsx` e `VehiclesEntityTable.tsx` + `EntityDetailsModal.tsx`.
- Novo `modules/settings/services/integrationService.ts` e tipos em `modules/settings/types/integration.ts`.
- Resultado: **a timeline e os logs de integração por entidade aparecem na UI**, com ação de retry. Testes em `__tests__/IntegrationTimeline.test.tsx`.

### Por que importa para o roadmap
É a primeira ferramenta de **troubleshooting/auditoria de falhas de integração nativa do produto**, fora do Sentry. Endereça parte da lacuna de "visibilidade de falhas de integração" mapeada no cronograma. Sugiro registrar como item de observabilidade aplicada na Onda correspondente do AutoChecker. Cobre: status por entidade, motivo do erro, status code HTTP, retry com 1 clique.

---

## 2. ⚠️ Alerta LGPD (auditado em separado)

O modelo `IntegrationLog` (`shared/models/integrations.py`, `db_table=integrations_log`) **persiste `request_payload` (JSON completo enviado ao ERP) e `response_body` (resposta completa do ERP)**, sem TTL/retenção, e o `IntegrationLogDetailSerializer` **expõe os dois na UI**. Como o payload carrega PII (CPF, CNH, nome, documentos), isso replica — agora num log de aplicação próprio — o mesmo padrão de risco já mapeado no Sentry (Etapa 7). **Ver auditoria dedicada:** `Auditoria_LGPD_IntegrationLog_AutoChecker_2026-06-30.md`.

---

## 3. Bloco LGPD / aceite digital (colateral de auditoria e segurança)

PRs 14944 / 15192 / 15195 / 15196 (backend + frontend) — "Aceite Digital de Termos e Política (LGPD)" e "auditoria forense do aceite":
- `LegalAcceptanceMiddleware` (enforcement do aceite no backend), interceptor 403, gate global de re-aceite.
- Captura de **IP + User-Agent reais** nos proxies de aceite (trilha de auditoria forense) e `user_cpf` como evidência.
- `f75496c` — **"remover backend_url leak em devtools"**: correção de vazamento de informação em devtools no frontend (higiene de segurança/observabilidade).

Relevância: trilha de auditoria (accountability, art. 6º X LGPD) e correção de info-leak — tangenciais à observabilidade, mas no mesmo eixo de governança.

---

## 4. CI do frontend — PR 14983

Adicionado step de **type-check no pipeline** (`typecheck` no `package.json` + etapa no CI). Qualidade; relevância indireta.

---

## O que NÃO mudou (e importa para o nosso escopo)

- **Sentry:** nenhuma alteração de DSN, settings, init ou instrumentação de erro nos repos do AutoChecker no período. A cobertura Sentry segue como no último snapshot.
- **Pilar de telemetria:** backend continua com `logging.getLogger` padrão; não houve adoção de logging estruturado JSON, métricas ou tracing novos.

---

## Referências cruzadas

- `Auditoria_LGPD_IntegrationLog_AutoChecker_2026-06-30.md` — auditoria LGPD do achado #2.
- `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` — caso análogo no Sentry.
- Memória: `autochecker-etapa7-analise-lgpd`, `autochecker-cronograma-workitems-azure`.

---

*Análise baseada em leitura direta dos diffs dos PRs 15213/15214 e do modelo/serializer `IntegrationLog`. Não foram lidos integralmente os arquivos não relacionados a observabilidade que vieram no mesmo PR 15213 (correção de extrator CVV/regex).*
