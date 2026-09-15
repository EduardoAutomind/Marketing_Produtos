# Onda 0 — AutoChecker · Etapas de baixo custo (quick wins)
> Análise: 2026-06-15 · Org Sentry: `automind-qd` · Base: detalhamento Ondas 0–3 (reav. 15/06) + verificação ao vivo do código em `Produtos\Autochecker`.
> Objetivo: apontar o que dá para **configurar/corrigir sem muito custo** na Onda 0.

## Recomendação principal — Item 6, parte "DisallowedHost" (custo praticamente zero)

É a única ação da Onda 0 que se resolve **só no painel do Sentry, sem mexer no código e sem deploy**.

- **O quê:** criar um *Inbound Filter* para `DisallowedHost`.
- **Por quê é barato:** configuração na UI do Sentry, reversível, sem build e sem risco de runtime.
- **Ganho imediato:** elimina ~**169 ocorrências/semana** de ruído de scanners de internet — `BACKEND-1A` (128 ev) + `BACKEND-17` (41 ev). São robôs batendo no IP cru, não falha nossa.
- **Estado (conferido ao vivo 15/06):** ainda não há filtro dedicado; o `before_send` (`base.py:713`) só trata `/health/` e blips de Redis.

## Dois wins baratos no mesmo nível

### 1. Item 6, parte "filtro de health morto" — correção de 1 linha (precisa deploy)
- Trocar `"/health/"` por `"/api/core/healthcheck/"` no `before_send` (`base.py:716`) e em `EXCLUDED_PATHS` (`api_logging.py:18`).
- Hoje o filtro "roda" mas **nunca casa** o endpoint real (`apps/core/urls.py:12` — confirmado), ou seja, dá falsa sensação de cobertura.
- **Custo:** 2 linhas + um deploy.

### 2. Item 3, lado Sentry — fechar a issue "tarefa fantasma" (1 clique)
- A `KeyError process_scheduled_notifications` (`WORKER-1F`, ~1.640 ev acumuladas) já está **morta** no código (task comentada em `notification_tasks.py:49-67`, dormente há 26 dias), mas segue `unresolved` no Sentry.
- Resolver/ignorar pela UI tira o maior ofensor histórico do backlog.
- ⚠️ O expurgo **completo** (registro órfão em `/tmp/celerybeat-schedule`) é trabalho de runtime/ops — esse **não** é barato; a limpeza no painel é grátis.

## Bônus que cruza Item 1 / alertas (painel, sem deploy)
- Adicionar **filtro de ambiente nas 3 regras de alerta** (hoje 1 por projeto, todas sem filtro). Faz o alerta parar de disparar com ruído de dev/staging — pré-requisito para alguém confiar e agir.

## O que NÃO é "barato" (para contraste)
| Item | Por que não é barato agora |
|---|---|
| **Item 4 — drift de migração** | Maior impacto, mas depende do time de Banco/Deploy (`migrate_schemas` + backfill); operação pesada/long-running. |
| **Item 2 — release/set-commits** | Exige mexer nas 4 pipelines Azure + decidir o frontend canônico (dois `next.config.js` divergentes). |
| **Item 1 — environment (lado deploy)** | Código pronto; falta garantir a env var nos pipelines (DevOps) e medir KPI ≥99%. |
| **Item 5 — consolidar init** | "Esforço P", mas trocar só a chamada **não** dá `CeleryIntegration` ao backend — precisa alterar o helper + deploy. |
| **Item 7 — PII/LGPD frontend** | `sendDefaultPii:true` ×3 + Replay sem masking; mexe em código de frontend + revisão de compliance. |
| **Item 8 — triagem do backlog** | Baixo custo técnico, mas é trabalho de pessoa (revisar issue a issue). |

## Sequência sugerida
1. **DisallowedHost Inbound Filter** — zero custo, hoje mesmo (painel).
2. **Fechar a `WORKER-1F`** — 1 clique (painel).
3. **Filtro de ambiente nos 3 alertas** — painel, sem deploy.
4. **Health path** (`base.py:716` + `api_logging.py:18`) — 2 linhas no próximo deploy.

> Os passos 1–3 limpam ~1.800 eventos de ruído **sem deploy e sem risco**. Citações `arquivo:linha` e IDs de issue conferidos contra o código e o Sentry ao vivo em 2026-06-15.
