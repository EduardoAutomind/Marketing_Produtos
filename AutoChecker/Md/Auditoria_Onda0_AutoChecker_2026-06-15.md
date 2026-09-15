# Auditoria de Conformidade — Onda 0 (Saneamento da Base)
## Cronograma de Observabilidade · AutoChecker × Azure DevOps

| | |
|---|---|
| **Data de geração** | 15/06/2026 |
| **Produto** | AutoChecker |
| **Ferramenta de observabilidade** | Sentry (org `automind-qd`) |
| **Fonte de verdade** | Azure DevOps — org `automindautomacao`, projeto `AutoChecker` (work items via REST API/WIQL) |
| **Escopo** | 8 etapas (itens 1 a 8 do cronograma) |
| **Total de work items no projeto** | 2.133 (consultados em 15/06/2026) |

> **Veredito-resumo:** a Onda 0 **NÃO está apta a ser considerada concluída**. Nenhuma das 8 etapas possui work item em estado *Done* cujo escopo cubra a etapa. **O gate deve permanecer FECHADO.**

---

## 1. Introdução

### O que é a Onda 0
A Onda 0 (Saneamento da Base) é o primeiro bloco do cronograma de observabilidade do AutoChecker e funciona como um **gate obrigatório**: enquanto não estiver concluída, as ondas seguintes (1 a 6) não devem avançar. Concentra a correção de configurações de ambiente/release no Sentry, a eliminação do ruído dominante e a triagem do backlog de issues.

### Regras da auditoria (invioláveis)
- **Única fonte de verdade: Azure DevOps.** Nada foi assumido por memória, inferência ou por descobertas de outras fontes (ex.: configuração de pipelines). Onde não houve work item, registra-se `[Não encontrado no Azure DevOps]`.
- Nenhuma etapa é declarada completa sem work item *Done* de escopo compatível.
- Ambiguidades são marcadas como `[Pendente de confirmação]`.

### Método de busca
1. **WIQL por título** (`[System.Title] CONTAINS '<termo>'`) com ~29 termos de alto sinal das 8 etapas → 130 matches.
2. **WIQL por descrição** (`[System.Description] CONTAINS WORDS '<termo>'`) com os termos técnicos exatos de cada etapa.
3. **Expansão das features guarda-chuva** e seus filhos:
   - Feature **40531** "Observabilidade" → filhos `48859, 40534, 51817, 40535, 40533, 40532`.
   - Bug **53700** "Estabilização de Issues Sentry — Maio/2026" → filhos `53701–53707`.
   - PBI **48859** "Sentry" → filho `48860`.
   - Bug **51817** "Sentry Erros" → filhos `51818, 51819, 51820, 51822`.

### Resultado-chave da busca por termos técnicos exatos (descrição + título)
| Termo | Ocorrências |
|---|---|
| `process_scheduled_notifications` | **0** |
| `init_sentry` | **0** |
| `CeleryIntegration` | **0** |
| `sendDefaultPii` | **0** |
| `set-commits` | **0** |
| `NEXT_PUBLIC_SENTRY_ENVIRONMENT` | **0** |
| `DisallowedHost` | **0** |
| `scrubbing` | **0** |
| `suspect commits` | **0** |
| `migrate_schemas` | 2 (`47359`, `47542` — contexto de unificação de auth) |
| `before_send` | 1 (`53665` — falso positivo, é sobre reconexão Redis) |
| `healthcheck` | 4 (`53997`, `53998`, `53910`, `53706`) |

> **Leitura:** os termos que definem o cerne técnico de cada etapa **não aparecem** em nenhum work item. Isso, por si só, indica que as etapas da Onda 0 não foram quebradas em itens dedicados e rastreáveis no Azure Boards.

### Legenda das classificações
| Classificação | Quando se aplica |
|---|---|
| ✅ **Concluída** | Work item *Done/Closed* e escopo bate com a etapa |
| 🔄 **Em andamento** | Work item *Active/In Progress/Em andamento* |
| 📋 **Planejada / Pendente** | Work item criado mas não iniciado (*To Do/New/Backlog*) |
| ❌ **Não mapeada** | Nenhum work item encontrado para a etapa |
| ⚠️ **Parcial / Ambígua** | Existe item, mas o escopo não cobre tudo ou o estado é ambíguo |
| 🔍 **Pendente de confirmação** | Item encontrado, mas não dá para confirmar que se refere a esta etapa |

---

## 2. Análise por etapa

### Etapa 1 — Padronizar tag `environment` nos 3 SDKs + isolar DEV/PRD
**Camada:** Frontend / Worker · **Esforço:** M

**Objetivo do cronograma:** garantir `environment ∈ {production, staging, development}` em backend, worker e frontend (hoje frontend ~15% production, worker ~65%); o frontend cai em fallback `"development"` quando `NEXT_PUBLIC_SENTRY_ENVIRONMENT` não está configurada no CI.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 44191 | Discovery | Done | Everton L. S. Silva | 2025-11-17 | Pesquisar e estudar melhor metodologia para gerar observabilidade |
| 44192 | Task | Done | Tarcisio Rocha | 2025-11-17 | Implementar método de observabilidade I |
| 44193 | Task | Done | Tarcisio Rocha | 2025-11-17 | Implementar método de observabilidade 2/3 |
| 46787 | Task | Done | Tarcisio Rocha | 2026-01-26 | Implementar método de observabilidade II |
| 44194 | Task | To Do | — | 2025-11-17 | Implementar método de observabilidade 3/3 |
| 48860 | Task | Done | Tarcisio Rocha | 2026-03-11 | Adicionar o Sentry aos Serviços (back/front/worker/custos OK; **scrapping pendente**) |

**Classificação:** 🔍 **Pendente de confirmação**

**Análise:** existem tarefas genéricas de "método de observabilidade" (algumas *Done*) e a inclusão do Sentry nos serviços (`48860`). Porém **nenhum work item trata especificamente** da padronização da tag `environment` nem da variável `NEXT_PUBLIC_SENTRY_ENVIRONMENT` no CI. Não é possível confirmar que o escopo desta etapa esteja coberto pelas tarefas genéricas.

**Pendências / Riscos:** sem item rastreável para a tag `environment`/fallback do frontend. Risco de o frontend continuar reportando como `development` em produção, poluindo a separação DEV/PRD no Sentry.

---

### Etapa 2 — Padronizar `release` + set-commits + isolar pipelines Azure
**Camada:** AutoChecker (transversal) · **Esforço:** M

**Objetivo do cronograma:** formato de release `<componente>@<hash>` nos 3 serviços, ativar `set-commits --auto` e corrigir os pipelines Azure; o frontend usa `org`/`project` de teste (`automind-teste` / `javascript-nextjs`) que enviam source maps para o projeto errado.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 36445 | Task | To Do | — | 2025-05-22 | Configuração do pipeline de releases no Azure DevOps |

**Classificação:** ⚠️ **Parcial / Ambígua**

**Análise:** o único work item relacionado (`36445`) trata genericamente de "pipeline de releases", está em *To Do* desde mai/2025 e **sem responsável**. Não há item algum para `set-commits`, source maps ou correção de `org`/`project` do Sentry. **Observação técnica (fora do Azure Boards):** a inspeção ao vivo dos pipelines mostrou release `backend@<hash>`/`worker@<hash>` já implementado via deploy SSH, mas isso **NÃO está refletido em nenhum work item** — logo, pela fonte de verdade desta auditoria, conta como não rastreado.

**Pendências / Riscos:** escopo coberto só de forma parcial e não iniciada nos Boards. `set-commits` (suspect commits) e `org`/`project` do frontend totalmente não mapeados.

---

### Etapa 3 — Limpar PeriodicTask órfã do Beat (KeyError `process_scheduled_notifications`)
**Camada:** Backend / Worker · **Esforço:** P

**Objetivo do cronograma:** remover/migrar a entrada órfã `process_scheduled_notifications` do `django-celery-beat` (gera ~1.541 KeyError por dispatch) e alinhar o schedule do DB com o código.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 53659 | Bug | **Done** | Tarcisio Rocha | 2026-05-18 | Limpar `beat_schedule` do backend e resetar `celerybeat-schedule` em prod |
| 40384 | Task | Done | Tarcisio Rocha | 2025-09-02 | Ajustar tasks do Celery BEAT |
| 53660 | Task | To Do | Tarcisio Rocha | 2026-05-18 | Limpar `beat_schedule` (Task duplicada da 53659, **aberta**) |
| 53707 | Task | To Do | — | 2026-05-19 | Limpeza preventiva do `celerybeat-schedule` no deploy (continuação de 53659) |

**Classificação:** ⚠️ **Parcial / Ambígua**

**Análise:** o núcleo do problema foi tratado — a Bug `53659` (*Done*) limpou o `beat_schedule` e resetou o `celerybeat-schedule` em produção. Porém **nenhum item nomeia a task órfã `process_scheduled_notifications` explicitamente** (correspondência por domínio, não literal), a Task-par `53660` ficou *To Do* (duplicidade não reconciliada) e a continuação `53707` (integrar a limpeza ao ciclo de deploy) segue *To Do*. A descrição de `53707` registra que o reset manual em prod só foi feito durante um incidente em 19/05.

**Pendências / Riscos:** falta a etapa preventiva no deploy (`53707`) e reconciliar a duplicata `53660`. Sem isso, a entrada órfã pode reaparecer em novos deploys.

---

### Etapa 4 — Corrigir migrações faltando em schemas de tenant (`migrate_schemas`)
**Camada:** Worker · **Esforço:** M

**Objetivo do cronograma:** o deploy roda apenas `migrate`/`migrate --plan`, nunca `migrate_schemas`, causando ~57 issues `relation … does not exist`. Adicionar `migrate_schemas` ao processo de deploy.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 51820 | Task | To Do | Tarcisio Rocha | 2026-05-04 | `relation "upload_document" does not exist` (issue do Sentry — sintoma exato) |
| 35848 | Task | To Do | — | 2025-05-12 | Testes de migração de schema em múltiplos tenants |
| 35829 | Task | **Removed** | Antonio M. B. Souza | 2025-05-12 | Estratégia para migrações de schemas de tenants (REMOVIDA) |

**Classificação:** ⚠️ **Parcial / Ambígua**

**Análise:** há um sintoma exato registrado (`51820`, "relation does not exist", em *To Do*) e tarefas antigas de estratégia/teste de migração de schema (`35829` removida, `35848` *To Do* de 2025). Mas **não existe work item para a correção sistêmica** pedida pela etapa: adicionar `migrate_schemas` ao deploy. As menções a `migrate_schemas` em `47359`/`47542` são de outro contexto (unificação de autenticação / tabela `User`).

**Pendências / Riscos:** a causa-raiz (deploy sem `migrate_schemas`) não tem item. Apenas sintomas isolados foram ticketados — as ~57 issues continuarão surgindo.

---

### Etapa 5 — Consolidar init no helper `init_sentry` + ativar CeleryIntegration no backend
**Camada:** Backend / Worker · **Esforço:** P

**Objetivo do cronograma:** backend e worker fazem `sentry_sdk.init()` de forma divergente; o backend só tem `DjangoIntegration` e `RedisIntegration`, sem `CeleryIntegration`. Consolidar ambos no helper `init_sentry` com as integrações corretas.

**Encontrado no Azure DevOps:** `[Não encontrado no Azure DevOps]` — busca por `init_sentry` e `CeleryIntegration` (título e descrição) retornou **zero** work items.

**Classificação:** ❌ **Não mapeada**

**Análise:** a única tarefa próxima (`48860`, *Done*) trata de "adicionar o Sentry aos serviços", não da consolidação do helper de init nem da `CeleryIntegration`. Nenhuma evidência rastreável.

**Pendências / Riscos:** etapa totalmente não mapeada. Sem `CeleryIntegration`, erros de tasks Celery podem não ser capturados/agrupados corretamente no Sentry.

---

### Etapa 6 — `before_send` / Inbound Filters: remover ruído de scanner, auth e health endpoint morto
**Camada:** Backend · **Esforço:** M

**Objetivo do cronograma:** filtrar `DisallowedHost` (127 ev), JWT/SchemaHeader (275 ev) e corrigir o filtro morto que tenta filtrar `/health/` quando o endpoint real é `/api/core/healthcheck/`.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 53661 | Bug | **Done** | Tarcisio Rocha | 2026-05-18 | Validar UUID no `_set_tenant_by_id` do `SchemaHeaderMiddleware` |
| 53662 | Task | To Do | Tarcisio Rocha | 2026-05-18 | Validar UUID no `SchemaHeaderMiddleware` (Task-par, aberta) |
| 53706 | Task | To Do | — | 2026-05-19 | Middleware: retornar 400 em rotas TENANT_APP sem header de tenant |
| 53684 | PBI | New | — | 2026-05-18 | [Infra] Implementar health check endpoint e monitoramento proativo |
| 53997 | Task | To Do | — | 2026-05-20 | [Infra] Criar endpoint `/healthcheck/detailed/` |

**Classificação:** ⚠️ **Parcial / Ambígua**

**Análise:** parte do ruído de SchemaHeader foi atacada na origem (`53661` *Done* valida UUID no middleware), o que reduz parte dos 275 eventos. Mas **não há item** para configurar `before_send`/Inbound Filters, nem para `DisallowedHost`, nem para corrigir o filtro morto `/health/` vs `/api/core/healthcheck/`. Os itens de healthcheck (`53684`/`53997`) **criam endpoints novos**, não corrigem o filtro do Sentry.

**Pendências / Riscos:** `before_send`, `DisallowedHost` e o filtro de health morto seguem não mapeados; o ruído dominante no Sentry não será eliminado só com `53661`.

---

### Etapa 7 — Scrubbing de PII/LGPD no Frontend + Data Scrubber
**Camada:** Frontend · **Esforço:** M

**Objetivo do cronograma:** o frontend tem `sendDefaultPii: true` nos 3 configs + `Sentry.setUser({email})` + Session Replay sem masking sobre telas de CNH/ASO/CPF. Corrigir a exposição de dados pessoais antes de qualquer expansão do Sentry.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 55050 | Feature | New | Gabriel S. B. Santos | 2026-06-09 | Aceite Digital de Termos e Política de Privacidade (LGPD) — **PRODUTO** |
| 55088 | PBI | New | Gabriel S. B. Santos | 2026-06-10 | Central de Ajuda autenticada (Portal LGPD do titular) — **PRODUTO** |

**Classificação:** ❌ **Não mapeada**

**Análise:** busca por `sendDefaultPii`, `scrubbing`, `data scrubber` e `PII` (título/descrição) **não retornou nenhum item ligado ao Sentry**. Os itens de LGPD encontrados (`55050`, `55088`) são de **produto** (aceite de termos, central de ajuda) e não tratam de mascarar PII no Sentry / Session Replay. Etapa não mapeada.

**Pendências / Riscos:** exposição de PII no Sentry (email do usuário no `setUser`, Session Replay sem masking de CNH/ASO/CPF) sem nenhum item de correção. **Risco legal/LGPD relevante.**

---

### Etapa 8 — Triagem ZERO do backlog (152 issues abertas no Sentry)
**Camada:** AutoChecker · **Esforço:** M

**Objetivo do cronograma:** hoje há 0 issues resolvidas em 30 dias. Realizar triagem completa do backlog, classificando como Resolvido, Ignorado, Em andamento ou Aguardando.

**Encontrado no Azure DevOps:**

| ID | Tipo | Estado | Responsável | Criado | Título |
|---|---|---|---|---|---|
| 53700 | Bug | New | — | 2026-05-19 | Estabilização de Issues Sentry — Maio/2026 (**guarda-chuva**, 7 filhos: 53701–53707) |
| 51817 | Bug | New | Tarcisio Rocha | 2026-05-04 | Sentry Erros (**guarda-chuva**, 4 filhos) |
| 51818 | Task | Done | Tarcisio Rocha | 2026-05-04 | Sentry — EnsureUserAndLogin duplicate key (resolvido) |
| 51819 | Task | To Do | Tarcisio Rocha | 2026-05-04 | `ModuleNotFoundError: No module named 'apps.validation.tasks.ocr'` |
| 51820 | Task | To Do | Tarcisio Rocha | 2026-05-04 | `relation "upload_document" does not exist` |
| 51822 | Task | To Do | Tarcisio Rocha | 2026-05-04 | Erro ao processar notificação |
| 53701–53707 | Task | To Do | vários | 2026-05-19 | 7 filhos de 53700 (notificações, WhatsApp, middleware — maioria *To Do*) |

**Classificação:** 🔄 **Em andamento**

**Análise:** existe esforço de triagem **ativo**: dois guarda-chuvas (`53700` "Estabilização de Issues Sentry" e `51817` "Sentry Erros") com filhos derivados de issues reais do Sentry. Porém ambos os guarda-chuvas estão *New*, poucos filhos estão *Done* (ex.: `51818`) e a maioria segue *To Do*. **Não é uma triagem completa fechada** do backlog de 152 issues — é uma triagem parcial e reativa.

**Pendências / Riscos:** a triagem não está concluída; o backlog completo não foi classificado. Guarda-chuvas abertos (*New*).

---

## 3. Resumo executivo

### Tabela de status geral

| # | Etapa | Classificação | Responsável (Azure) | Risco principal |
|---|---|---|---|---|
| 1 | Tag `environment` + isolar DEV/PRD | 🔍 Pendente de confirmação | Tarcisio Rocha (genéricos) | Frontend pode reportar como `development` em prod |
| 2 | Release + set-commits + pipelines | ⚠️ Parcial/Ambígua | — (36445 sem dono) | set-commits / source maps / org errado não mapeados |
| 3 | PeriodicTask órfã do Beat | ⚠️ Parcial/Ambígua | Tarcisio Rocha | Prevenção no deploy aberta; órfã pode voltar |
| 4 | `migrate_schemas` no deploy | ⚠️ Parcial/Ambígua | Tarcisio Rocha (sintoma) | Causa-raiz das ~57 issues sem item |
| 5 | `init_sentry` + CeleryIntegration | ❌ Não mapeada | — | Erros de Celery podem não ser capturados |
| 6 | `before_send` / Inbound Filters | ⚠️ Parcial/Ambígua | Tarcisio Rocha (parcial) | Ruído dominante (scanner/auth/health) segue |
| 7 | Scrubbing PII/LGPD no Frontend | ❌ Não mapeada | — | **Risco legal:** PII exposta no Sentry/Replay |
| 8 | Triagem ZERO do backlog | 🔄 Em andamento | Tarcisio Rocha | Triagem parcial; backlog não fechado |

### Contagem por classificação
- ✅ Concluídas: **0**
- 🔄 Em andamento: **1** (E8)
- 📋 Planejadas/Pendentes: **0**
- ❌ Não mapeadas: **2** (E5, E7)
- ⚠️ Parciais/Ambíguas: **4** (E2, E3, E4, E6)
- 🔍 Pendente de confirmação: **1** (E1)

### Diagnóstico geral
- **A Onda 0 está apta a ser considerada concluída?** **NÃO.** Zero etapas com work item *Done* cobrindo o escopo.
- **Etapas bloqueadoras para avançar para a Onda 1:** todas as 8, por ausência de evidência de conclusão. As mais críticas são a **Etapa 5** (`init_sentry`/CeleryIntegration — sem item) e a **Etapa 7** (PII/LGPD — sem item e com risco legal), além da **Etapa 6** (ruído dominante não eliminado) e da **Etapa 8** (triagem não fechada).
- **Risco de avançar sem concluir a Onda 0:** **Alto.** Sem saneamento, as ondas seguintes seriam construídas sobre dados de Sentry poluídos (ruído de scanner/auth/health), ambiente mal classificado, releases sem rastreabilidade de commit e exposição de PII — comprometendo métricas, alertas e conformidade LGPD.

### Recomendações prioritárias
1. **Criar work items rastreáveis para as 8 etapas.** Hoje as etapas da Onda 0 **não existem como itens dedicados** no Azure Boards — a auditoria não pode ser fechada por falta de rastreabilidade. Quebrar a Feature `40531` (Observabilidade) em 8 itens, um por etapa.
2. **Tratar com urgência a Etapa 7 (PII/LGPD no Sentry).** Risco legal, zero mapeamento: desativar `sendDefaultPii`, remover email do `setUser` e aplicar masking no Session Replay sobre telas de CNH/ASO/CPF.
3. **Reconciliar os pares Bug(Done)+Task(To Do) duplicados e fechar a triagem.** Pares como `53659`/`53660` e `53661`/`53662` deixam o estado real ambíguo; os guarda-chuvas de triagem (`53700`, `51817`) seguem *New*. Alinhar os estados para que o Boards reflita a realidade.

---

## 4. Itens `[Pendente de confirmação]`
- **Etapa 1:** as tarefas "método de observabilidade I/II/2-3" (`44192`/`44193`/`46787`, *Done*) **podem** cobrir a padronização da tag `environment`, mas **não há evidência direta** — não dá para confirmar o escopo.
- **Etapa 3:** a Bug `53659` (*Done*) limpou o `beat_schedule`, mas **nenhum item nomeia `process_scheduled_notifications` explicitamente** — a correspondência é por domínio (celery beat), não literal.

## 5. Limitações da auditoria
- O PAT utilizado **não tem escopo de Service Connections nem de Variable Groups** (retornaram 401), mas isso não afeta esta auditoria, que é baseada em **work items** (escopo Work Items Read, OK).
- A busca por descrição usa full-text (`CONTAINS WORDS`), que tokeniza termos com `_`/`-`; termos como `process_scheduled_notifications` podem não casar mesmo se citados de forma fragmentada — por isso a confirmação cruzada por título e pelos guarda-chuvas.
- Achado metodológico central: **as 8 etapas da Onda 0 praticamente não existem como work items dedicados** no Azure Boards. O que existe é trabalho genérico de observabilidade (adicionar Sentry — *Done*) e correção reativa de erros. Isso, por si só, impede declarar o gate como concluído.

---

## 6. Artefatos gerados
- **PDF:** `Auditoria_Onda0_AutoChecker_2026-06-15.pdf`
- **Markdown (este arquivo):** `Auditoria_Onda0_AutoChecker_2026-06-15.md`
- **Pasta:** `Cronograma observabilidade/AutoChecker/`

*Auditoria baseada exclusivamente em work items do Azure DevOps (org `automindautomacao`, projeto `AutoChecker`), consultados via REST API/WIQL em 15/06/2026.*
