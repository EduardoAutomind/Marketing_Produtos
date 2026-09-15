# Auditoria de Conformidade do Cronograma de Observabilidade — AutoLoad V4 **contra o código-fonte**

> **Documento:** parecer de auditoria de conformidade dos cronogramas de observabilidade do AutoLoad V4 confrontados, etapa a etapa, com o **código real**.
> **Organização Sentry:** `automind-qd`
> **Fonte da verdade:** código em `C:\Projetos\automind-obs\Produtos\Autoload V4` (Backend .NET 8, Frontend Next.js 14, EdgeGateway .NET 8 Worker, Portal).
> **Alvos auditados:**
> 1. **Definitivo** — `Cronograma_Definitivo_Observabilidade_AutoLoad_V4.md` + planilha gerada por `gerador de relatorios/_gerar_xlsx_cronograma_definitivo.py` (abas Cronograma · Visão geral · Marcos · Riscos · KPIs; `F1.1…F3.10`; `R1…R10`).
> 2. **Revisado (Ondas)** — `Cronograma_Observabilidade_AutoLoad_V4_Revisado_2026-06-02.xlsx` (abas Cronograma · Legenda e Contexto · Ações da Ata; Ondas 0–6).
> **Data:** 08/06/2026

---

## Nota de método

A auditoria anterior (`Auditoria_Cronograma_Observabilidade_AutoLoad_V4_2026-06-02.md`) validou o cronograma contra **documentação + snapshot ao vivo do Sentry** — e diz isso explicitamente. Esta auditoria faz a passada que faltava: **abre o código e confronta cada afirmação verificável**. Regra de ouro: nenhuma afirmação aqui sem origem em um arquivo aberto; o que depende de painel/processo/runtime é marcado `❓ NÃO VERIFICÁVEL` (não é erro do cronograma).

**Legenda de veredito:** ✅ Conforme · ⚠️ Divergente · 🟦 Já concluído · ❓ Não verificável no código · ➕ Faltando.

---

## 1. Resumo

| Veredito | Definitivo (F/R) | Revisado (Ondas) |
|---|---|---|
| ✅ Conforme | F1.2, F1.3, F1.9, F2.3, F2.5, F2.x restantes | #2 (release), #11, #16(/health), demais ondas |
| ⚠️ Divergente | **F1.1, F1.5, F1.6, F1.7 / R6** | **#1, #3, #6, #7, #10** |
| 🟦 Já concluído / improcedente | **F1.8 / R8** | **#4 (MQTT)** |
| ❓ Não verificável (painel/processo) | F1.4, F1.10, F1.11, R1, R3, R5, R9, R10, KPIs de cobertura | #5, #8, #15, #17, #25 |
| ➕ Faltando | (ver § 4) | (ver § 4) |

**Achado de maior peso:** o "bug" do MQTT (`F1.8`/`R8` no Definitivo; item #4 no Revisado) é **improcedente** — o código já usa `-=`. Era a correção de "custo trivial / impacto direto" mais citada nos dois cronogramas e nas priorizações de semana 1.

---

## 2. Conformidade item a item (evidência no código)

### 2.1 Bug `MQTTService.RemoveMessageHandler` — 🟦 IMPROCEDENTE/CONCLUÍDO
- **Afirmação dos cronogramas:** usa `+=` em vez de `-=` → memory leak + handlers duplicados (Definitivo `F1.8`/`R8`; Revisado #4, "Bug de código confirmado (G9)").
- **Código:** ambos os serviços removem o handler **rastreado** com `-=`:
  - Backend — `AUTOLOAD_V4_Backend/AutoloadV4.Domain.Operations/Services/MQTTService.cs:106`: `MqttClient.ApplicationMessageReceivedAsync -= _currentHandler;`
  - Edge — `AUTOLOAD_V4_EdgeGateway/AutoloadV4.EdgeGateway/Services/MQTTService.cs:98`: idem.
  - O `+=` que aparece (`:91` / `:85`) é a **inscrição** em `SetMessageHandler`, que antes faz `-=` do handler anterior (`:77` / `:72`). O design é documentado nos XML-docs (`removemos pelo _currentHandler rastreado`).
- **Veredito:** premissa de bug não confere. **Reclassificado para Concluído / Encerrado (criticidade Baixa)**; ação residual = teste de regressão subscribe/unsubscribe.

### 2.2 `BeforeSend` / PII — ⚠️ DIVERGENTE (parcialmente concluído)
- **Afirmação:** "ausência de `BeforeSend` global" (R6/G15); "`SendDefaultPii=false` nos 3 SDKs" (Revisado #6); "`SendDefaultPii` não declarado" (R6).
- **Código:**
  - Frontend **já tem** `beforeSend` com scrubbing de chaves sensíveis (`password|token|secret|authorization|api_key|bearer|credential` → `[REDACTED]`) nos três runtimes: `AUTOLOAD_V4_Frontend/src/instrumentation-client.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`. E usa **`sendDefaultPii: true`** (não false).
  - EdgeGateway tem `SetBeforeSend` (tags `serviceName/siteId/gatewayId/tenantId`) em `Worker/Program.cs:43-50` e `SendDefaultPii: false` no `appsettings.json`.
  - Backend **não tem** `beforeSend` — captura via `ExceptionMiddleware.cs:13-22` (`SentrySdk.CaptureException` com tags `tenantId`/`userId`).
- **Veredito:** a lacuna real é **o Backend (.NET)** e o **scrubbing de PII de domínio** (CPF/placa/motorista — diferente das chaves de credencial que o FE já cobre). Corrigido o texto de F1.7/#6 e a evidência de R6.

### 2.3 `environment` — ⚠️ DIVERGENTE (valores)
- **Afirmação:** `environment ∈ {production, staging, development, kiosk}` (F1.1; tags globais; Revisado #1).
- **Código/spec:** os valores canônicos são **`dev` / `hml` / `prd`** — `AUTOLOAD_V4_Specs/docs/decisions/features/20260303_sentry_environment_tags/ESPECIFICACAO.md` § 4 (tabela de pipeline ADO). O KIOSK é módulo à parte (React/Vite), distinguido por `service`/tag. Backend (`Program.cs:61`) e Edge (`Worker/Program.cs:19`) hoje lêem `Sentry:Environment`; a spec pede `Logging:Automind:Context:env`.
- **Veredito:** valores corrigidos para `{dev, hml, prd}`. A **cobertura** real (Backend 0% em prd) permanece `❓ NÃO VERIFICÁVEL` no código (é estado de runtime no painel).

### 2.4 Source maps — ⚠️ DIVERGENTE (já instrumentado no código)
- **Afirmação:** configurar `@sentry/webpack-plugin` / `sentry-cli` upload no pipeline + `withSentryConfig({hideSourceMaps:true})` (F1.5; Revisado #7).
- **Código:** `AUTOLOAD_V4_Frontend/next.config.mjs:16-52` já usa `withSentryConfig(...)` com `widenClientFileUpload: true` (`:31`), `org`/`project` por env, `silent: !process.env.CI` (`:25` — faz upload no CI), `tunnelRoute`, `automaticVercelMonitors`.
- **Veredito:** a instrumentação de upload **já existe**. O sintoma `Object.s` (60 issues) é consistência de **release/authToken no pipeline** → `❓ NÃO VERIFICÁVEL` no código. Nota: `hideSourceMaps` explícito não está setado (usa default).

### 2.5 `release` — ⚠️ DIVERGENTE/Conforme (existe no código)
- **Afirmação:** Definitivo `R5`/`F1.6` — "release tag inconsistente"; Revisado #2 — "release JÁ existe (SENTRY_RELEASE)".
- **Código:** release **existe**:
  - Edge — `Worker/Program.cs:40`: `options.Release = $"AutoloadV4.EdgeGateway.Worker@{release}"` (versão do assembly).
  - Frontend — injetado no build via `withSentryConfig`.
  - Backend — não seta `options.Release` (grep sem ocorrência); confia em auto-detecção de `SENTRY_RELEASE` (documentado em `Autoload_V4-documentacao.md:287`, formato `<comp>@<hash>`).
- **Veredito:** o Revisado #2 está **correto** (release existe). O Definitivo `F1.6`/`R5` deve enquadrar como **padronização/`set-commits`/isolamento de pipeline**, não criação. A "inconsistência Linux+Windows" é `❓ NÃO VERIFICÁVEL` (painel/pipeline).

### 2.6 Isolar DEV/PRD — ⚠️ DIVERGENTE (Revisado: arquivo/mecanismo)
- **Afirmação (Revisado #3):** `enabled = (NODE_ENV === 'production')` no `sentry.client.config.ts`.
- **Código:** o arquivo de client é `src/instrumentation-client.ts` (Next 14), e o gate real é **validação de placeholder de DSN** (`!dsn.includes("#")` / DSN não injetado ⇒ SDK no-op) — não `NODE_ENV`. Backend/Edge desabilitam quando `Sentry:Dsn` é placeholder (`#{...}#`).
- **Veredito:** corrigido nome de arquivo + mecanismo no Revisado. (O Definitivo `F1.2` é genérico — "separar DSN ou desabilitar SDK local" — e permanece ✅.)

### 2.7 Módulo SDK do EdgeGateway — ⚠️ DIVERGENTE (Revisado #10)
- **Afirmação:** criar módulo SDK do Edge ("a onda 1 original não tinha módulo próprio para o Edge").
- **Código:** o Edge **já inicializa** Sentry — `Worker/Program.cs:30-52`: `logging.AddSentry(...)` com `Dsn` (gate por placeholder), `EnableLogs`, `Environment`, `options.Release` e `SetBeforeSend` (tags globais).
- **Veredito:** ação é **estender** (tags de domínio, PII), não criar do zero.

### 2.8 `/health` — ✅ CONFORME (pendência real)
- **Código:** sem `AddHealthChecks`/`MapHealthChecks`/`IHealthCheck` no Backend (grep sem ocorrência). F1.9 e item #16 estão corretos como pendência.

### 2.9 Política de captura do Frontend — ✅ já implementada
- **Código:** `AUTOLOAD_V4_Frontend/src/services/api.ts:188-199` captura `status >= 500 || status === 404` e **exclui 401/403** — exatamente a política descrita nos cronogramas. Em código, já está pronto.

### 2.10 EF Core / `Sentry.EntityFramework` — ✅ CONFORME (pendência)
- **Código:** sem `Sentry.EntityFramework`/`AddEntityFramework` no Backend (grep sem ocorrência). F2.3 correta como pendência.

### 2.11 Backend SDK / ExceptionMiddleware — ✅ CONFORME
- **Código:** `Program.cs:51-71` configura `UseSentry` (gate por placeholder de DSN); `ExceptionMiddleware.cs` trata `ServiceException`/`PermissionDeniedException`/genérica com tags. F1.3 (filtrar/`drop` de `ServiceException`) permanece pendência válida.

---

## 3. Itens `❓ NÃO VERIFICÁVEL` no código (painel/processo/runtime)

Não são erros do cronograma — apenas estão fora do alcance do repositório:

- Cobertura real de `environment` (Backend 0% em prd) — estado no painel.
- Loop `AUTOLOADV4-EDGEGATEWAY-2V` (14.686 ev./30d) e projeção de cota — métrica do Sentry.
- Regras de alerta, supressão, roteamento — config de painel.
- Triagem das 349 issues — processo.
- Upload de source maps efetivo / Release Health / "suspect commits" — pipeline + painel.
- Vazamento real de PII em produção — amostragem de eventos.

---

## 4. ➕ Sugestões (FALTANDO) — para aprovação

- **Padronizar a fonte de `environment` (Backend e Edge):** hoje lêem `Sentry:Environment`; a spec `20260303` pede `Logging:Automind:Context:env`. Item de baixo custo que fecha a divergência spec×código. (Toca F1.1.)
- **`sendDefaultPii: true` no Frontend:** revisar explicitamente sob a ótica LGPD (o scrubbing atual cobre credenciais, não PII de domínio). (Reforça F1.7.)
- **`options.Release` explícito no Backend:** hoje depende de auto-detecção de `SENTRY_RELEASE`; tornar explícito alinha com o Edge e remove ambiguidade. (Toca F1.6.)

---

## 5. Pendências `[Não verificável nas fontes]`

- Propagação `sentry-trace`/`baggage` no MQTT (F2.1): a `AutoloadV4.Lib.MqttRpc` é citada como "Fase 4" no `Worker/Program.cs:60`, mas a propagação de trace ponta-a-ponta não foi confirmada nesta passada — tratada como pendência (não como divergência).
- Instrumentação do Portal Cliente (F2.14/#25): o projeto `AUTOLOAD_V4_Portal` está vazio no checkout (só `README`); `frequency=0` é config de alert rule (painel). Sem base de código para verdicto.

---

## 6. Veredito final

Os dois cronogramas acertam o **enquadramento** (lêem bem a Ata, o Questionário e o snapshot). Confrontados com o código, porém:

- **1 achado improcedente/concluído:** o bug do MQTT (`-=` já correto) — era item de semana 1 nos dois.
- **Divergências factuais:** valores de `environment` (`dev/hml/prd`), `BeforeSend`/PII (FE já cobre credenciais; lacuna é o Backend), source maps (já instrumentado no código), `release` (existe; falta padronizar), e — só no Revisado — nome de arquivo do client e a premissa de "Edge sem módulo SDK".
- **O restante é pendência válida** (/health, EF Core, tracing MQTT) ou **fora do alcance do código** (painel/processo).

Artefatos corrigidos entregues: `Cronograma_Definitivo_Observabilidade_AutoLoad_V4_REVISADO.xlsx`, `Cronograma_Observabilidade_AutoLoad_V4_Revisado_2026-06-08.xlsx` e o `.md` Definitivo (banner de revisão no topo).
