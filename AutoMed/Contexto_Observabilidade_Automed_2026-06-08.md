# Contexto da Implantação de Observabilidade — Automed

> **Para quem é este documento:** todo o time que vai trabalhar na implantação de observabilidade do Automed — de quem nunca tocou no produto a quem vai operar o cronograma. Ao terminar a leitura, você deve entender o que é o Automed, por que estamos fazendo observabilidade agora, o estado atual, a arquitetura, o que será entregue, em que sequência e prazo, quem faz o quê e quais são os riscos.
>
> **Produto:** Automed · **Ferramenta central:** Sentry (org `automind-qd`, projeto `automed`) · **Data-base:** 08/06/2026.
>
> **Fontes (cruzadas):** documentação técnica do produto, snapshot ao vivo do Sentry (janela 01→07/06/2026) e estudo estático de oportunidades (14/04/2026) — ver §14. Onde uma informação não existe nas fontes, está marcado **[Pendente / não encontrado nas fontes]**.

---

## 1. Visão geral — o que é o Automed

O **Automed** (Automed.Nuvem) é uma plataforma cloud-native de **gestão metrológica e conformidade regulatória** para a indústria de **óleo e gás (upstream) no Brasil**. Baseado na norma ABNT NBR ISO 10.012, garante rastreabilidade metrológica dos sistemas de medição fiscal e **automatiza a geração e o envio de arquivos regulatórios à ANP** (Agência Nacional do Petróleo) via **i-Engine** (fonte: documentação de produto).

- **Multi-tenant** = vários clientes ("organizações") no mesmo sistema, com isolamento por `OrganizacaoId` (campo em todos os models) **e por schema de banco por organização** (confirmado pelo Sentry — ver §5).
- **Por que medição importa:** os dados de produção e os arquivos ANP são **dado regulatório** — uma falha silenciosa de sincronização ou um arquivo rejeitado/fora de prazo pode gerar **multa e auditoria**, mesmo com volume baixo de eventos.

**Estado atual do produto:**

- **Em produção**, atendendo clientes reais (o Sentry registra eventos de organizações reais, com schemas próprios — ex.: `db5cd138903b59527ee0c4840913c0b8`).
- **Observabilidade parcial e em "modo instalação".** Diferente do que dizia o estudo de abril, **o Sentry JÁ está instalado e capturando na API** (.NET) desde **14/04/2026** — mas sem triagem, sem alertas, sem isolamento de ambiente, sem contexto de tenant e com **Workers e Frontend ainda cegos ou parciais**.

> **Onde o Automed aparece no Sentry:** um único projeto — `automed` (platform `dotnet-aspnetcore`, org `automind-qd`). **Não há** projeto de frontend nem projeto dedicado de workers.

---

## 2. Por que observabilidade agora — motivação e urgência

**O problema de hoje:** a equipe só descobre uma falha **quando o cliente reporta** — ou nem isso, no caso dos Workers, que logam no **Windows Event Viewer** sem agregação nem alerta. Evidências concretas das fontes (janela 01→07/06/2026):

- **0 issues resolvidas / 18 abertas** — não há fluxo de triagem ativo (Sentry).
- **0 regras de alerta** mirando o projeto `automed` — a única regra do org cobre `autoloadv4-edgegateway` e os projetos do AutoChecker, **não** o Automed (Sentry).
- **Ruído de configuração domina o sinal:** os maiores ofensores da semana são **bugs de versão de banco** — colunas que o código referencia mas não existem (`AceitoUsuario`, `enviado`) e uma **tabela ausente num schema de organização** (`monitoramentos`) — somando **mais de 300 eventos** que afogam os incidentes reais.
- **Risco regulatório invisível:** erros do fluxo ANP (arquivo inválido, BTP/BSW duplicados) aparecem com baixo volume e sem contexto de negócio — exatamente o tipo de evento que precisa de rastreabilidade para auditoria.

**A urgência:** o Automed é um sistema **regulado** em produção. Sem observabilidade saneada, o tempo até detectar um incidente (MTTD) depende de o cliente ligar, e o tempo até resolver (MTTR) é alto porque falta contexto (qual organização? qual unidade? qual versão?).

---

## 3. Objetivos da implantação (em ordem de prioridade)

1. **Sanear a base** (pré-requisito de tudo): ambiente correto por evento, release padronizado, eliminar os bugs/ruídos dominantes (schema drift + migração por organização + ruído de host), reclassificar erros de domínio esperados e tratar PII. Sem isso, qualquer métrica é estatisticamente sem sentido.
2. **Enxergar erros de verdade**: dar contexto/tags de tenant (organização) e **estender a cobertura aos Workers e ao Frontend** — hoje cegos.
3. **Detectar antes do cliente**: alertas por ambiente, health check, uptime e cron monitors dos 3 Workers, plugados num canal que o suporte recebe.
4. **Rastrear ponta a ponta**: tracing API ↔ Workers (Refit) e **centralizar os logs dos Workers** (hoje no Event Viewer).
5. **Medir o negócio**: métricas por organização e por fluxo (Sync → Tasks → ANP); dashboards.
6. **Endurecer**: rastreabilidade regulatória ANP, conectividade XConnect/PI e segurança adjacente.

> Esta ordem é a própria sequência das **7 ondas** do cronograma (§8).

---

## 4. Escopo

**Entra (espinha dorsal — Sentry como observabilidade de aplicação + negócio):**

- Saneamento do que a **API** já captura (environment, release, ruído, domínio, PII, triagem).
- **Cobertura dos componentes cegos**: 3 Workers (Sync/Tasks/FileExporter) e Frontend Angular 13.
- Contexto de tenant (organização) em todos os eventos.
- Alertas por ambiente, health/uptime/cron monitors; tracing API↔Workers; centralização de logs.
- Métricas de negócio por organização e por fluxo; dashboards no Sentry.
- Rastreabilidade do fluxo regulatório ANP.

**Fica de fora ou em trilha separada:**

- **Métricas de infraestrutura** (CPU, memória, disco das VMs/Windows Services) — não fazem parte deste cronograma; ficam para uma trilha de Prometheus/Grafana ou Application Insights. **[Escopo de infra não detalhado nas fontes.]**
- **Reescrita funcional do produto**: correções de bug entram apenas quando são causa de ruído/cegueira (ex.: schema drift, migração por organização, ruído de host).
- **Acesso ao banco do cliente (XConnect):** a instrumentação de conectividade depende de não expor a `ConnectionString` — tratada como dado sensível.

---

## 5. Estado atual da observabilidade (gap analysis)

Com base no snapshot Sentry (01→07/06) + doc + estudo estático:

| Aspecto | O que JÁ existe | O que FALTA |
|---|---|---|
| SDK Sentry | **API .NET instalada** (`automed`, dotnet-aspnetcore) desde 14/04/2026, capturando exceções não tratadas | **Workers** (Sync/Tasks/FileExporter) parciais ou no Event Viewer; **Frontend Angular sem Sentry** (cego) |
| Captura de exceção | Exceções não tratadas da API + alguns processos do `Tasks.Core` | Catch dos Workers só faz `Logger.LogError()` (estudo #3/#4); frontend Angular sem `ErrorHandler` |
| `environment` | 1 environment: `production` | **QA/HOMOLOG/DEV não isolados** — não emergem ou caem como production |
| `release` | `latestRelease` presente | Sem `release`/`AppVersion` consistente; builds de 2 agentes Azure (`AgentBuild1`/`AgentBuild2`) coexistindo |
| Tags de tenant | — | `OrganizacaoId`/`usuario` **não populados** → `userCount=1` em todas as issues (estudo #2) |
| Schema de banco | Schema por organização (multi-tenant) | **Migração não chega a todos os schemas** (`<hash>.monitoramentos` ausente); **colunas ausentes** (`AceitoUsuario`, `enviado`) — código à frente do DB |
| Performance/tracing | `TracesSampleRate` previsto no init (estudo #1, 0.1) | Sem tracing API↔Workers; queries estourando `Execution Timeout` |
| Logs | Workers no **Windows Event Viewer** | Sem agregação central nem correlação log↔erro (Automed **não** tem Loki como o AutoChecker) |
| Alertas | 1 regra no org (não cobre `automed`) | **0 regras** para o Automed; sem filtro de ambiente, sem canal, sem N1/N2/N3 |
| Health/Uptime | — | **Sem endpoint `/health`** (estudo #9); sem Uptime Monitor |
| Cron Monitors | `hasMonitors = False` | Nenhum check-in dos 3 Workers (estudo #8) |
| Triagem | — | **0 issues resolvidas / 18 abertas** |

---

## 6. Arquitetura técnica do Automed

Baseado na documentação técnica + evidência dos stacktraces no Sentry.

| Componente | O que é | Stack | Sentry |
|---|---|---|---|
| **API** | Backend REST por domínio (Auth, Eventos, Entidades, Documentos, Tarefas, Organização…) | **.NET 8 / ASP.NET Core** (21 projetos C#), JWT, Refit, Swashbuckle | `automed` (instalado) |
| **Models Layer** | Clean Architecture (Domain · Business Services · DAL Repository/Unit of Work) — **compartilhada por API e Workers** | C# 12, EF Core | via `automed` |
| **Sync.Worker** | Orquestrador de coleta: **XConnect** (lê SQL Server do cliente/Weatherford), **PI System** (OSIsoft PI AF), **Scan** (CSV OMNI70/711/712) → `POST /eventos` (Refit) | .NET 8 Windows Service | Event Viewer / a confirmar |
| **Tasks.Worker** | Polling da **fila de tarefas no banco a cada 5s**; instancia `IProcesso` por reflection | .NET 8 Windows Service | **parcial** (erros do `Tasks.Core` aparecem) |
| **FileExporter.Worker** | Loop **diário (24h)**: exporta XMLs ANP para o sistema de arquivos | .NET 8 Windows Service | Event Viewer / a confirmar |
| **Frontend** | SPA do cliente | **Angular 13** + PrimeNG, Bootstrap, Chart.js | **nenhum** (cego) |

**Banco:** SQL Server / **Azure SQL**, schema principal `automed` + **schemas por organização**; modelo **híbrido relacional + JSON** (colunas JSON em Entidades e Eventos); migrations via EF Core.

**Fluxo de negócio:** Frontend → **API REST** → regras na **Models Layer** → persiste → **Workers** fazem integração/cálculo/sync/tarefas → **envio e consulta à ANP** → resultado volta via frontend/notificação. **Os Workers consomem a API via Refit + JWT — não acessam o banco direto.**

**Conformidade ANP (o motivo de existir):** `AnpService` integra o **i-Engine da ANP** (SOAP/XML): `EnviarArquivo()`, `RetornarProtocolo()`, `RetornarSituacao()`. Fluxo `ArquivoAnp` (carregado) → `ValidarArquivoAnp` → válido/inconsistente → `EnviarArquivo` → enviado/rejeitado → `AtualizarSituacaoArquivo` (aceito/aceito_parcial/rejeitado). **Erro regulatório tem impacto de multa/auditoria mesmo com volume baixo.**

**Logs:** os 3 Workers logam no **Windows Event Viewer** (Application Log, source `Automind.Automed.Sync.PI [Ambiente] [Versão]`) — **sem agregação central**. O projeto Sentry cobre sobretudo a **API**.

---

## 7. Camadas de observabilidade (o que cada uma entrega ao Automed)

| Camada | O que é | Entrega específica ao Automed |
|---|---|---|
| **Captura de erros** | Registrar exceções com contexto | Erros da API + dos 3 Workers (sync, tarefas, ANP) e do frontend Angular passam a aparecer com organização/unidade |
| **Performance / tracing** | Latência e seguir uma operação entre serviços | Latência de endpoints críticos (/eventos, /entidades) por organização; trace de um ciclo de sync (coleta → POST API → persistência) |
| **Logs correlacionados** | Ligar log estruturado ao erro | Centralizar os logs dos Workers (hoje Event Viewer) e saltar do erro no Sentry ao log da mesma execução |
| **Métricas de negócio** | Indicadores do produto | Produção sincronizada/dia por unidade; arquivos ANP gerados/enviados/aceitos/rejeitados; tarefas executadas vs falhas |
| **Alertas** | Notificar a falha proativamente | Regras por `environment:production`, roteadas a Slack/Teams + ticket, segmentadas por N1/N2/N3 |
| **Health / uptime** | Saber se o sistema está de pé | Uptime Monitor sobre `/health` e **Cron Monitors dos 3 Windows Services** |

---

## 8. Cronograma — ondas, entregas e prazos

Fonte: `Cronograma_Observabilidade_Automed_2026-06-08.xlsx` (aba *Cronograma*). **7 ondas · 29 itens.** **Semanas são relativas** (Sem 1..14) — a âncora de calendário ainda **[não definida nas fontes]**. **Esforço:** P ≤ 1 dia · M = 2–5 dias · G > 5 dias. **Responsável de todos os itens: "A definir"** (ver §10).

> **Onda 0 é um GATE:** nenhuma ampliação (alertas, tracing, métricas) antes de concluir o saneamento.

| Onda | Semanas | Foco | Itens | "Pronto" quando… |
|---|---|---|---|---|
| **0 — Saneamento** | 1–2 | environment, release, schema drift, migração por organização, ruído de host, reclassificação de domínio, PII, triagem | 1–8 | base limpa: ≥99% dos eventos com `environment` correto; ruído dominante (~470 ev) eliminado; 0 issues sem status |
| **1 — Fundação dos SDKs e Cobertura** | 3–4 | tags de tenant, cobertura dos 3 Workers, instrumentar Frontend Angular, política de envio | 9–12 | Workers e Frontend instrumentados; organização em todos os eventos |
| **2 — Contexto e Agrupamento** | 4–6 | instrumentar pipeline de sync, capturar excepts silenciosos, fingerprint de cálculo | 13–15 | sync rastreável por unidade/dia; excepts dos Workers chegam ao Sentry |
| **3 — Alertas + Health** | 6–8 | N1/N2/N3, regras por ambiente, /health + uptime, cron monitors, canal | 16–20 | alertas acionáveis em produção chegando ao N1; 3 Workers com cron monitor |
| **4 — Performance + Logs** | 8–10 | timeouts de SQL, tracing API↔Workers, centralizar logs | 21–23 | trace API↔Worker + salto erro↔log centralizado |
| **5 — Métricas + Dashboard** | 10–12 | métricas de negócio, dashboard por organização/fluxo | 24–25 | dashboard por organização e por fluxo exibível |
| **6 — Endurecimento + Regulatório** | 12–14 | rastreabilidade ANP, conectividade XConnect/PI, desvios, segurança | 26–29 | rejeição/prazo ANP alertados; conectividade por organização monitorada |

> **KPI explícito:** "≥99% dos eventos com `environment` correto em 7 dias" (item 1). Demais critérios de pronto por item: ver coluna *Observações/Evidência* da planilha e o documento de **Detalhamento das Etapas**.

---

## 9. Análise de conformidade (síntese)

O cronograma foi montado cruzando o **estudo estático de abril** com a **realidade do Sentry de junho**. A correção de premissa mais importante:

| Tema | Estudo de abril dizia | Realidade (Sentry/doc, junho) |
|---|---|---|
| **Instalação do Sentry** | "Sentry **NÃO** está instalado em **nenhum** componente" | A **API .NET JÁ captura** desde 14/04/2026 (projeto `automed`). Foco muda de "instalar do zero" para **sanear + estender** cobertura |
| **Cobertura dos Workers** | Workers totalmente silenciosos | **Erros do `Tasks.Core` JÁ aparecem** no Sentry; Sync (XConnect/PI/Scan) e FileExporter **a confirmar** |
| **Nomes dos 3 Workers** | Sync.Worker, Tasks.Worker, **XConnect.Worker** | Doc validada: Sync.Worker (orquestra XConnect/PI/Scan), Tasks.Worker, **FileExporter.Worker** — XConnect é sub-worker do Sync |
| **Ruído dominante** | Não previsto (sem dados ao vivo) | **Schema drift** (`AceitoUsuario`/`enviado`, ~247 ev) + **migração por organização** (`monitoramentos`, ~71 ev) + **ruído de host** (`https port`, 107 ev) — os três maiores ofensores, só visíveis no Sentry |

**Itens do estudo que permanecem válidos e foram incorporados:** tags de tenant (item 2 → cronograma 9), capturar erros silenciosos dos Workers (3/4 → 14), instrumentar sync de produção (5 → 13), conectividade XConnect (6 → 27), importação ANP (7 → 28), cron monitors (8 → 19), health endpoint (9 → 18), desvios de medição (10 → 28), performance (11 → 21), brute-force (12 → 29).

---

## 10. Papéis e responsabilidades

- **Responsáveis por item:** **"A definir" em todas as 29 linhas** — decisão consciente (equipe ainda não atribuída). **[Nomes: Pendente.]**
- **Níveis N1/N2/N3 de suporte:** **ainda não definidos** — defini-los é o **item 16** (Onda 3) e é **gate** da ativação dos alertas. **[Mapeamento: Pendente.]**
- **CODEOWNERS:** previsto no item 20 (ainda não configurado).

---

## 11. Riscos e bloqueadores

| Risco / Bloqueador | Por que importa | Dependência crítica |
|---|---|---|
| **Schema drift código×banco** | `AceitoUsuario`/`enviado` ausentes afogam o sinal (~247 ev) e indicam deploy à frente da migração | Item 3 (Onda 0) — alinhar migração×deploy |
| **Migração não chega a todos os schemas** | `monitoramentos` ausente em schema de organização (~71 ev) — algumas organizações sem tabela | Item 4 (Onda 0) |
| **`environment` não isolado** | 1 só environment (`production`); QA/HOMOLOG contaminam ou somem | Item 1 (Onda 0) — gate de tudo que mede produção |
| **Workers e Frontend cegos** | Falha de sync/ANP some no Event Viewer; erro Angular não chega ao Sentry | Itens 10 e 11 (Onda 1) |
| **Domínio tratado como error** | Auth/validações esperadas (~70+ ev) inflam ruído e fadiga de alerta | Item 6 (Onda 0) |
| **Sem alerta para o Automed** | Projeto fora de qualquer regra → ninguém é avisado | Item 17 (Onda 3) |
| **Risco regulatório ANP** | Rejeição/prazo perdido = multa/auditoria, mas hoje invisível | Item 26 (Onda 6) |
| **ConnectionString do XConnect** | Dado sensível — jamais pode ir aos breadcrumbs/eventos | Itens 13/27 (atenção de PII) |
| **Responsáveis "A definir"** | Sem dono, o cronograma não executa | §10 |

---

## 12. Glossário

- **Sentry** — plataforma de monitoramento de erros e performance.
- **Issue / evento** — agrupamento de ocorrências similares / cada captura individual.
- **Tag** — rótulo no evento para filtrar/agrupar (ex.: `organizacao_id`, `environment`).
- **`environment`** — ambiente de origem (`production`, `homolog`, `qa`, `development`).
- **`release` / `AppVersion`** — versão do código que gerou o evento; correlaciona erro × deploy.
- **PII / LGPD** — dado pessoal identificável / lei de proteção de dados.
- **Tracing / `trace_id` / span** — seguir uma operação entre serviços / id do trace / trecho do trace.
- **`TracesSampleRate`** — fração de transações enviadas (0.0–1.0).
- **Breadcrumb** — "migalha" de contexto registrada antes do erro.
- **Fingerprint** — regra de agrupamento de eventos numa issue.
- **Health check / Uptime Monitor / Cron Monitor** — endpoint de saúde / verificação periódica / vigia de job agendado.
- **MTTD / MTTR** — tempo médio para detectar / resolver um incidente.
- **N1 / N2 / N3** — níveis de suporte (triagem → técnico → especialista).
- **XConnect** — sistema externo (Weatherford/Halliburton) de onde o Sync lê produção via SQL Server.
- **PI System** — historiador OSIsoft (PI AF Server / PI Points) de dados de processo.
- **ANP / i-Engine** — Agência Nacional do Petróleo / serviço SOAP de recepção dos arquivos regulatórios.
- **Refit** — cliente HTTP tipado em .NET (os Workers usam para chamar a API).
- **EF Core / migration** — ORM do .NET / script de evolução de schema.
- **Schema por organização** — isolamento multi-tenant: cada organização tem seu namespace de tabelas no SQL Server.

---

## 13. Próximos passos (para começar)

1. **Atribuir responsáveis** aos itens da Onda 0 e **definir N1/N2/N3** (item 16).
2. **Ancorar o cronograma no calendário** (definir a Semana 1).
3. **Atacar a Onda 0 (gate)** — começar pelos bugs de maior impacto: **schema drift** (item 3) e **migração por organização** (item 4), que são corrigíveis e removem a maior parte do ruído; depois **environment** (1), **release** (2) e **ruído de host** (5).
4. **Confirmar a cobertura real dos 3 Workers e do Frontend** (itens 10/11) — saber exatamente o que já chega ao Sentry.
5. **Confirmar `SendDefaultPii=false`** e garantir que a `ConnectionString` do XConnect nunca vá aos eventos (item 7).
6. **Revogar/rotacionar** qualquer Auth Token do Sentry exposto e padronizar a entrega de tokens de forma segura.

---

## 14. Referências (arquivos-fonte)

| Fonte | Caminho |
|---|---|
| Planilha de cronograma | `Cronograma Observabilidade/AutoMed/Cronograma_Observabilidade_Automed_2026-06-08.xlsx` |
| Cronograma (HTML/PDF) | `Cronograma Observabilidade/AutoMed/Cronograma_Observabilidade_Automed_2026-06-08.{html,pdf}` |
| Detalhamento das etapas | `Cronograma Observabilidade/AutoMed/Detalhamento_Etapas_Cronograma_Observabilidade_Automed_2026-06-08.md` |
| Documentação de produto (referência) | `.claude/skills/produtos-automind/references/automed.md` |
| Documentação de produto (PDF) | `Produtos/Automed-documentacao.pdf` |
| Estudo estático de oportunidades | `Estudo de melhoria de observabilidade/Oportunidades de Melhoria de Observabilidade - Automed.md` (14/04/2026, 12 itens) |
| Snapshot Sentry | `gerador de relatorios/_data_2026-06-01__2026-06-07/` (projeto `automed`: 18 issues) |

### Divergências entre fontes (identificadas no cruzamento)

1. **Sentry instalado:** o estudo de abril dizia "não instalado em nenhum componente"; o **código real da API já captura** desde 14/04/2026 (o estudo foi escrito no dia da instalação).
2. **Workers:** o estudo lista `XConnect.Worker` como um dos 3 Windows Services; a doc validada tem **`FileExporter.Worker`** como o terceiro, com XConnect/PI/Scan como **sub-workers do Sync**.
3. **Ruído dominante:** invisível ao estudo estático (sem dados ao vivo) — o Sentry revela **schema drift + migração por organização + ruído de host** como os três maiores ofensores.

> **Observação operacional:** os artefatos do cronograma do Automed ficam em `Cronograma Observabilidade/AutoMed/`. As contagens de evento referem-se à janela **01→07/06/2026** (7 dias); a tendência de 30 dias deve ser confirmada no próximo snapshot.
