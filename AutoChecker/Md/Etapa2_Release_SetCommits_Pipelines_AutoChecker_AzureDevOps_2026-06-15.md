# Análise — Etapa 2 do Cronograma de Observabilidade (AutoChecker) · revisão ao vivo no Azure DevOps

> **Item #2 — "Padronizar release `<comp>@<hash>` + set-commits + isolar pipelines Azure"**
> Onda 0 (Saneamento da Base) · Esforço M · Status no cronograma: **Não iniciado**

**Data da análise:** 2026-06-15
**Supera/complementa:** `Etapa2_Release_SetCommits_Pipelines_AutoChecker.md` (2026-06-11), que só olhou os `next.config.js` e deixou os itens #1 (parte server) e #3 marcados como "não dá pra atestar por esses arquivos". Esta revisão fecha esse gap com dados **ao vivo** do Azure DevOps.

**Fontes desta análise (as 3 fontes da etapa):**
1. **Código real (pipelines YAML, ao vivo no Azure DevOps)** — org `automindautomacao`, projeto `AutoChecker`, baixados via REST API para `Cronograma observabilidade/AutoChecker/_azdo_yaml/`.
2. **Documentação** — `Cronograma_Observabilidade_AutoChecker_2026-06-03.xlsx`, aba *Cronograma*, item #2.
3. **Config do Azure DevOps ao vivo** — build definitions, triggers, pools, environments (REST API `_apis/build/definitions`, `_apis/pipelines/environments`).

> ⚠️ Método: dados puxados por **REST API do Azure DevOps autenticada por PAT** (não há MCP de Azure). Não é "scrape" da UI — é a API oficial, retorno JSON. Reproduzível com o PAT em `.azdo_pat.txt` (gitignored).

---

## 0. O que existe de verdade no Azure DevOps (vs. o que o cronograma assume)

A etapa fala em **"isolar as 4 pipelines (backend, frontend, worker, tests)"**. A realidade é outra:

| # | Build definition (id) | Repo de origem | YAML | Observação |
|---|---|---|---|---|
| 1 | **Backend** (431) | `AutoChecker` (monorepo) | `backend.azure-pipelines.yml` | deploy via SSH |
| 2 | **Worker** (430) | `AutoChecker` (monorepo) | `worker.azure-pipelines.yml` | deploy via SSH |
| 3 | **Frontend** (428) | `AutoChecker` (monorepo) | `frontend.azure-pipelines.yml` | deploy DigitalOcean |
| 4 | **AutoChecker_Frontend** (491) | `AutoChecker_Frontend` (repo separado) | `azure-pipelines.yml` | deploy DigitalOcean |
| 5 | **AutoChecker_Frontend** (492) | `AutoChecker_Frontend` (repo separado) | `azure-pipelines-validate.yml` | só testes de PR |
| 6 | **AutoChecker_APP** (487) | `AutoChecker_APP` | `app.azure-pipelines.yml` | **placeholder "Hello world"** (não faz nada) |

**Discrepâncias com o cronograma (flag: Sei — confirmado ao vivo):**
- **Não existe pipeline "tests" dedicada.** Os testes são *stages* dentro de cada pipeline (`stage: Test` → `pytest`/`vitest`). O item #2 conta uma pipeline que não existe.
- **São 6 definitions, não 4** — e duas se chamam `AutoChecker_Frontend`.
- **Confirmado no nível de pipeline o problema dos "dois frontends":** a pipeline `Frontend` (428) builda o frontend **dentro do monorepo `AutoChecker`**, enquanto `AutoChecker_Frontend` (491) builda um **repo Git separado**. Triggers divergem (`dev`/`main` vs `develop`/`main`) e empurram para **repos GitHub diferentes** (`automindssa/AutoChecker` vs `automindssa/AutoChecker_Frontend`). São dois caminhos de deploy de frontend vivos ao mesmo tempo.
- **`AutoChecker_APP` (Expo/mobile)** existe e não é citado em lugar nenhum da etapa; hoje é um YAML starter que só dá `echo Hello, world!`.

---

## 1. Release `<comp>@<hash>` — PARCIAL (2 de 3, e falta justo o frontend)

A descoberta nova vs. 11/06: **backend e worker JÁ setam o release** no formato pedido — mas no **servidor**, durante o deploy SSH, não via `sentry-cli` no CI.

| Serviço | Release `<comp>@<hash>`? | Evidência |
|---|---|---|
| **backend** | ✅ `backend@<short-hash>` | `_azdo_yaml/AutoChecker__backend.azure-pipelines.yml:139-141` (dev) e `:219-221` (prod) — `COMMIT_HASH=$(git rev-parse --short HEAD)` + `sed` em `backend/.env` |
| **worker** | ✅ `worker@<short-hash>` | `_azdo_yaml/AutoChecker__worker.azure-pipelines.yml:135-137` (dev) e `:186-188` (prod) |
| **frontend** | ❌ inexistente | nem `frontend.azure-pipelines.yml` nem `AutoChecker_Frontend/azure-pipelines.yml` setam `SENTRY_RELEASE`/`release` — só sincronizam com GitHub e deixam o DigitalOcean buildar |

**Veredito #1: PARCIAL.** O formato `<comp>@<hash>` está padronizado em backend e worker; **o frontend não tem release nenhum** — e é exatamente o componente que também tem o `org/project` errado no `withSentryConfig` (ver #4). Isso é uma **mudança** vs. o doc de 11/06, que dava release como "❌ inexistente" nos três.

> 🐞 **Bug real no worker em produção** (`worker.azure-pipelines.yml`, job `DeploySSH`, branch `main`):
> - linha **183**: `git pull origin dev` — o deploy de **produção puxa a branch `dev`**.
> - linha **188**: grava `SENTRY_RELEASE` em **`worker/.env.dev`**, mas o `docker compose` de prod usa **`.env.prod`** (linha 195). Ou seja, em prod o release é escrito no arquivo errado e provavelmente **não chega ao container**.
> O backend faz certo (`git pull origin $GITHUB_BRANCH` / `main`). Confiança: **alta** (está explícito no YAML).

---

## 2. `set-commits --auto` (suspect commits) — ❌ NÃO CUMPRIDA

**Não há `sentry-cli` em nenhuma das 6 pipelines.** `SENTRY_RELEASE` é apenas uma variável de ambiente consumida pelo SDK em runtime; **ninguém associa os commits ao release** (`sentry-cli releases set-commits --auto` ou `new-deploy`). Sem isso, o Sentry **não consegue apontar o "suspect commit"** — que é justamente o ganho da etapa.

**Veredito #2: NÃO CUMPRIDA.** Confiança: **alta** (ausência verificada nos 6 YAMLs).

---

## 3. Isolar pipelines Azure — ❌ NÃO CUMPRIDA (separação por componente existe; isolamento dev/prod não)

O que a etapa quer ("máquina dev não publica no produtivo") precisa ser relido: **não há agente de máquina dev** — tudo roda no pool hospedado `Azure Pipelines` (ubuntu-latest). O risco real aqui é **dev e prod compartilharem a mesma pipeline sem gate**.

**Evidências ao vivo:**
- **0 Environments no projeto** (`_apis/pipelines/environments` → `count: 0`). ⇒ **não existe nenhum gate de aprovação/checks** antes do deploy de produção. Confiança: **alta**.
- **dev e main na mesma pipeline.** Cada pipeline tem `trigger` em `dev` **e** `main`; o deploy de prod é separado **só por `condition: eq(Build.SourceBranchName,'main')`** (ex.: `backend:197`, `worker:165`). Qualquer push na `main` publica em produção, sem aprovação humana.
- **Worker dev usa a connection do backend:** `sshEndpoint: "backend-dev"` no job de worker dev (`worker.azure-pipelines.yml:115`) — connections cruzadas entre serviços.
- **Connections SSH em uso** (nomes extraídos dos YAMLs): `backend-dev`, `backend-prod`, `ssh-service-connection-worker`. A configuração interna delas **não pôde ser verificada** (o PAT não tem escopo de Service Connections → 401). Flag: **Não sei** (config das connections).
- Todas as 6 definitions: `queueStatus: enabled`, pool compartilhado, trigger `continuousIntegration`.

**Veredito #3: NÃO CUMPRIDA.** Há *separação por componente* (pipelines distintas por serviço), mas **não há isolamento dev↔prod**: mesma pipeline, gate só por nome de branch, **sem Environments/aprovações**, e ainda o bug do worker que mistura dev em prod. Confiança: **alta** para o que foi verificado por API/YAML; **parcial** para a config interna das connections.

---

## 4. `org`/`project` do `withSentryConfig` (frontend) — ❌ continua errado (herdado do doc de 11/06)

Isto vive no `next.config.js`, não no Azure — então **não é verificável por estas fontes**. Mantém-se o veredito do doc anterior: ainda `org:'automind-teste'` / `project:'javascript-nextjs'` nos dois `next.config.js`. Flag: **Parcial** (não revalidei o arquivo nesta sessão; ver `Etapa2_..._2026-06-11.md`).

> Nota relevante descoberta agora: as pipelines de frontend **não rodam `sentry-cli` nem upload de source maps no CI** — o `withSentryConfig` só age no build do **DigitalOcean**. Logo, corrigir `org/project` no código continua sendo o ponto-chave do frontend; o CI não compensa isso.

---

## 5. Veredito consolidado

| Entrega da Etapa 2 | Situação (ao vivo, 2026-06-15) | Δ vs. 11/06 |
|---|---|---|
| release `<comp>@<hash>` | **PARCIAL** — backend ✅, worker ✅ (bug em prod), frontend ❌ | era "❌ nos 3" |
| set-commits (suspect commits) | **❌ NÃO CUMPRIDA** — sem `sentry-cli` | igual |
| isolar pipelines (dev↔prod) | **❌ NÃO CUMPRIDA** — 0 environments, gate só por branch | agora confirmado por API |
| org/project no frontend | **❌/Parcial** — vive no `next.config.js` | não revalidado nesta sessão |
| **Status geral** | **❌ Em aberto, mas mais avançado do que a planilha diz ("Não iniciado")** | backend/worker já fazem release |

---

## 6. Achados extra (reais, fora do escopo estrito da etapa, mas relevantes)

1. **Segredo embutido + history overwrite.** As pipelines sincronizam Azure→GitHub com `git remote add origin https://rochaTarcisio:$(GITHUB_TOKEN)@github.com/...` e **`git push --force`** após `rm -rf .git; git init` (ex.: `frontend:113-116`, `backend:103-106`, `worker:98-101`). Sobrescreve o histórico do GitHub a cada deploy e expõe o token na URL do remote (mascarado em log, mas é padrão frágil).
2. **Modelo de deploy real:** Azure roda testes → espelha código no GitHub (force push) → **SSH no droplet** → `git pull` + `docker compose`/`systemctl`. O build acontece **no servidor de destino**, não no agente. Isso muda *onde* o `set-commits` deve rodar (precisa do histórico git — melhor no CI, antes do mirror destrutivo).
3. **`AutoChecker_APP` (491→ 487)** é só placeholder; se entrar no radar de observabilidade, hoje não tem nada.

---

## 7. Plano de resolução (concreto, na ordem)

### Passo 1 — Frontend: fechar release + org/project (o elo mais fraco)
- Corrigir `org`/`project` nos `next.config.js` (ver doc de 11/06, Passo 1).
- Definir `SENTRY_RELEASE=autochecker-frontend@<hash>` no build (no `app-*.yml`/DigitalOcean ou via `withSentryConfig.release.name`), para alinhar com backend/worker.

### Passo 2 — set-commits no CI (os 3 serviços)
- Adicionar um step `sentry-cli releases new "<comp>@$HASH"` + `sentry-cli releases set-commits "<comp>@$HASH" --auto` + `finalize`, **antes** do `rm -rf .git` (senão perde o histórico). Token via variável secreta do CI (`SENTRY_AUTH_TOKEN`), não no código.

### Passo 3 — Corrigir o bug do worker em prod
- `worker.azure-pipelines.yml` job `DeploySSH`: trocar `git pull origin dev` → `git pull origin main` (linha 183) e gravar em `worker/.env.prod`, não `.env.dev` (linha 188). Sem isso, prod do worker está rodando dev.

### Passo 4 — Isolamento dev↔prod de verdade
- Criar **Environments** `autochecker-prod` (e `-dev`) no Azure DevOps com **approval check** no de produção.
- Converter os jobs de deploy de prod em **deployment jobs** (`environment: autochecker-prod`) para passar pelo gate.
- Revisar as service connections: separar a connection do worker da do backend (`backend-dev`) e restringir cada uma ao seu servidor.

### Passo 5 — Decidir o frontend canônico (conecta com Passo 0 do doc de 11/06)
- Há **duas** pipelines de frontend vivas apontando para repos diferentes. Definir qual é produção e **desabilitar/arquivar a outra** (`queueStatus`), senão telemetria e deploy continuam ambíguos.

---

## 8. Ressalvas / o que NÃO foi verificado (flag: Não sei)

- **Config interna das service connections** (`backend-dev`, `backend-prod`, `ssh-service-connection-worker`): PAT sem escopo (401). Não sei se há restrição de quem pode usá-las.
- **Variable groups / Library**: idem 401 — não inspecionei. As variáveis vistas (`GITHUB_TOKEN`, `DO_TOKEN`, `SSH_PRIVATE_KEY`, `DEV_APP_ID`, `PROD_APP_ID`…) vêm do nível da definition (confirmado via `_apis/build/definitions`).
- **Branch policies** dos repos (proteção de `main`): não consultadas nesta rodada.
- **`next.config.js`**: não relido ao vivo hoje; veredito do frontend herda o doc de 11/06.
