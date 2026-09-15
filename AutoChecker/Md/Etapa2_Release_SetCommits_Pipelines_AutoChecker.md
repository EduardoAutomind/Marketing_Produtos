# Análise — Etapa 2 do Cronograma de Observabilidade (AutoChecker)

> **Item #2 — "Padronizar release `<comp>@<hash>` + set-commits + isolar pipelines Azure"**
> Onda 0 (Saneamento da Base) · Esforço M · Status no cronograma: **Não iniciado**

**Data da análise:** 2026-06-11
**Fontes analisadas:**
- `Produtos/Autochecker/AutoChecker_Frontend/next.config.js`
- `Produtos/Autochecker/AutoChecker/frontend/next.config.js`
- `Cronograma observabilidade/AutoChecker/Cronograma_Observabilidade_AutoChecker_2026-06-03.xlsx` (aba *Cronograma*, item #2)

---

## 1. Os dois `next.config.js` — são quase gêmeos

| | `AutoChecker_Frontend\next.config.js` | `AutoChecker\frontend\next.config.js` |
|---|---|---|
| `withSentryConfig` | ✅ presente | ✅ presente |
| `org` default | `"automind-teste"` ❌ | `"automind-teste"` ❌ |
| `project` default | `"javascript-nextjs"` ❌ | `"javascript-nextjs"` ❌ |
| `release` definido | ❌ não existe | ❌ não existe |
| `set-commits` | ❌ não existe | ❌ não existe |
| `compiler.removeConsole` | ✅ tem (linhas 8-13) | ❌ não tem |
| resto (`images`, `rewrites`, `tunnelRoute`, `hideSourceMaps`, etc.) | idêntico | idêntico |

A **única** diferença real entre eles é o bloco `compiler.removeConsole` (que limpa `console.*` em produção, exceto `error`/`warn`). No mais, são cópias.

Pelo `CLAUDE.md`, a estrutura oficial do projeto é `AutoChecker/frontend/` — ou seja, o `AutoChecker_Frontend/` é provavelmente uma cópia antiga/duplicada.

> ⚠️ **Isso já é um problema em si:** ter dois `next.config.js` divergentes significa que dá pra buildar a partir do diretório errado e mandar telemetria pro lugar errado.

---

## 2. O que a Etapa 2 (item #2) exige

> **"Padronizar release `<comp>@<hash>` + set-commits + isolar pipelines Azure"**
> (Onda 0, esforço M, Status: *Não iniciado*)

Quatro entregas:

1. **Formato de release consistente** `<componente>@<hash>` nos 3 serviços (backend / worker / frontend).
2. **`set-commits --auto`** ativado → habilita *suspect commits* (Sentry aponta o commit que provavelmente causou o erro).
3. **Isolar as 4 pipelines Azure** (backend, frontend, worker, tests) — máquina dev não pode publicar no projeto produtivo.
4. **Corrigir o org/project default do `withSentryConfig`** no frontend — hoje `'automind-teste'/'javascript-nextjs'`; sem `SENTRY_ORG`/`SENTRY_PROJECT` no CI, **source maps e releases vão para o projeto ERRADO**.

---

## 3. Veredito: ❌ NÃO cumprida

Olhando só o que dá pra verificar nesses arquivos (a parte #4, e indícios de #1/#2):

- **org/project errados** → confirmado nos **dois** arquivos. Continua `automind-teste` / `javascript-nextjs`. O correto, pelo próprio cronograma (org **`automind-qd`**, projeto **`autochecker-frontend`**), não está lá.
- **release `<comp>@<hash>`** → não há nenhuma chave `release` no `withSentryConfig`. Não padronizado.
- **set-commits** → ausente.
- **isolamento de pipelines** → não é configurável aqui (fica no Azure DevOps), então não dá pra atestar por esses arquivos — mas o status global do item é *Não iniciado*.

> O status "Não iniciado" da planilha bate com o código: **a etapa não foi tocada.**

---

## 4. Como fazer — plano concreto

### Passo 0 — Decidir o diretório canônico
Confirmar que `AutoChecker/frontend/` é o de produção e **deletar/arquivar `AutoChecker_Frontend/`** (ou vice-versa). Não dá pra manter dois `next.config.js` divergentes.
*(Envolve apagar pasta → precisa de OK explícito.)*

### Passo 1 — Corrigir o `withSentryConfig` (a parte que mora nesses arquivos)
Trocar os defaults errados pelos certos e adicionar `release`:

```js
module.exports = withSentryConfig(nextConfig, {
  org: process.env.SENTRY_ORG || "automind-qd",
  project: process.env.SENTRY_PROJECT || "autochecker-frontend",
  authToken: process.env.SENTRY_AUTH_TOKEN,
  release: {
    name: process.env.SENTRY_RELEASE, // formato: autochecker-frontend@<git-hash>
    setCommits: { auto: true },        // suspect commits
  },
  silent: !process.env.CI,
  widenClientFileUpload: true,
  tunnelRoute: "/monitoring",
  hideSourceMaps: true,
  webpack: { treeshake: { removeDebugLogging: true } },
});
```

### Passo 2 — Definir `SENTRY_RELEASE` na pipeline do frontend
Como `autochecker-frontend@$(git rev-parse --short HEAD)`, e garantir que `SENTRY_ORG`/`SENTRY_PROJECT`/`SENTRY_AUTH_TOKEN` venham do CI (não do default do código). Isso fecha a parte de "isolar pipelines" do lado do frontend: **só o CI tem o token.**

### Passo 3 — Replicar release `<comp>@<hash>` no backend e worker
(Python SDK) para o formato ficar consistente nos 3 serviços — isso conecta com o **item #5 da Onda 0** (consolidar o init do Sentry).

### Passo 4 — Isolar as 4 pipelines Azure
(Config no Azure DevOps, fora desses arquivos): bloquear envio a partir de máquinas dev e separar os ambientes.

---

## 5. Ressalvas / pontos a confirmar antes de mexer

- O `withSentryConfig` mantém **`hideSourceMaps: true`** e `widenClientFileUpload: true` — **preservar**.
- Confirmar os valores **`automind-qd`** (org) / **`autochecker-frontend`** (project) — deduzidos do próprio cronograma, mas é o tipo de coisa que tem que estar 100% certa, senão a telemetria some.
- Decidir qual diretório de frontend é o canônico (Passo 0) antes de aplicar o Passo 1.

---

## 6. Resumo executivo

| Entrega da Etapa 2 | Situação |
|---|---|
| org/project correto no frontend | ❌ ainda `automind-teste`/`javascript-nextjs` |
| release `<comp>@<hash>` | ❌ inexistente |
| set-commits (suspect commits) | ❌ inexistente |
| isolar pipelines Azure | ❌ não iniciado (fora desses arquivos) |
| **Status geral** | **❌ Não cumprida — "Não iniciado" confere com o código** |
