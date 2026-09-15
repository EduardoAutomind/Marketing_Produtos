# Questionário de Triagem do Sentry — Perguntas + Respostas do Time de Dev

> **Contexto:** follow-up da apresentação do Sentry. O Suporte montou um questionário de 16 perguntas para organizar os alertas e melhorar a análise; o time de Produtos respondeu.
> **Org Sentry:** `automind-qd` · **Produtos:** AutoLoad V4 (V4) · Automed · AutoChecker
> **Thread:** "RE: V4 - Logs (troubleshoot) - Suporte"

---

## Participantes

- **Remetente do questionário:** Fabio Daniel — *Product Support & Infrastructure Support - Leader* (Suporte)
- **Respostas (e-mail de 2026-05-13 11:16):** Gustavo Schmal (Produtos)
- **Cópia:** Raian Almeida, Edson Neto, Eduardo Santos, Leandro Lima Ramos, Victor Hugo Nascimento Silva, Daniel Almeida, Lucas Ricardo da Silva, Larissa Santana

---

## Resumo de pendências (consolidado pelo time)

| # | Pendência | Responsável |
|---|-----------|-------------|
| 1 | Modificar o Frontend para habilitar nível de log configurável por deploy | Produtos |
| 2 | Documentar política de envio de eventos por camada e ambiente | Produtos |
| 3 | Adicionar registro de `release` (requer releases estabilizadas) | Produtos |
| 4 | Configurar o Sentry: agrupamento de erros | Suporte |
| 5 | Configurar o Sentry: notificações e alertas | Suporte |
| 6 | Correlação correção de defeitos vs. deploys | Suporte |

**Bloqueador transversal:** o campo `release` ainda **não está configurado**. Sem ele, o Sentry não associa automaticamente em qual deploy um erro foi introduzido/resolvido — o que prejudica o workflow de resolução (Q12–14) e a correlação picos × deploys (Q16).

---

## Bloco 1 — O que está sendo enviado ao Sentry?

### Q1. Qual é o critério atual para um evento ser enviado ao Sentry? Existe uma política definida?
*Muitos projetos enviam tudo sem triagem — essa pergunta abre o diagnóstico.*

**Resposta:**
- **Backend:** sem política formal. Todo erro que passa pelo `ExceptionMiddleware` é enviado sem triagem — `ServiceException`, `PermissionDeniedException` e `Exception` genérica. Não há `BeforeSend` com lógica de filtro, nem `MinimumEventLevel` explícito.
- **Frontend:** política implícita no `api.ts` — apenas erros HTTP **≥ 500** e **404** são capturados via `captureException`. Erros **401 e 403** são explicitamente excluídos. O `beforeSend` sanitiza dados sensíveis, mas não descarta eventos.
- **EdgeGateway:** `MinimumEventLevel` é configurável via placeholder de deploy (`#{SENTRY_EVENT_LEVEL}#`). Em dev usa `"Information"`; em produção depende do pipeline substituir o valor. Se o placeholder não for substituído, cai no default do Sentry (`Error`).
- **Pendência:** modificar o Frontend para depender do deploy e documentar a política.

### Q2. Estamos capturando apenas erros não tratados ou também exceções capturadas manualmente com `Sentry.captureException`?
*Exceções tratadas capturadas manualmente multiplicam o volume rapidamente.*

**Resposta:** Ambos.

### Q3. Temos logs de nível `info` ou `debug` sendo enviados em produção?
*Esses níveis devem ficar fora do Sentry em ambiente produtivo.*

**Resposta:** Logs habilitados nas 3 camadas (backend, frontend e edgegateway).
**Pendência:** habilitar configuração do nível de log com dependência do ambiente (dev, hml, prd).

### Q4. Existem erros esperados ou de terceiros (bots, crawlers, extensões de browser) entrando como ruído?
*Podem representar 30–50% do volume em sistemas web.*

**Resposta:** Não há filtros definidos no backend e frontend. A infraestrutura está confiando nos filtros estabelecidos nas configurações do CloudFlare.

---

## Bloco 2 — Organização e contexto dos eventos

### Q5. Temos environments configurados corretamente? (production, staging, development separados)
*Sem isso, erros de dev poluem a análise de produção.*

**Resposta:** Sim — os ambientes são configurados via variáveis definidas no deploy de cada camada. Por padrão: **dev, hml e prd**.

### Q6. Usamos o campo `release` para identificar a versão do sistema em cada evento?
*Permite comparar erros antes e depois de um deploy.*

**Resposta:** **Pendência.** Requer configuração alinhada com o registro da release, assim que tivermos as releases estabilizadas.

### Q7. Adicionamos tags customizadas nos eventos? (ex: módulo, tipo de usuário, funcionalidade)
*Tags são o principal recurso para filtrar eventos por contexto de negócio.*

**Resposta:**
- **Backend:**
  - `tenantId` — do header `Tenant` da requisição
  - `userId` — de `context.User.Identity.Name`
  - `errorMessage` — mensagem traduzida do erro
  - `worker` — nome do worker (`MQTTWorker`, `ProgramWorker`, `JobExecutionWorker`)
  - Extra: `requestPath`
- **Frontend:**
  - `errorType` — categoria do erro (`api_error`, `network_error`, `download_error`, etc.)
  - `statusCode` — código HTTP da resposta
  - Contexto de usuário via `setUser`: `id`, `email`, `username`, `tenant`, `tenantName`
- **EdgeGateway** (mais completo dos três):
  - Global via `BeforeSend`: `serviceName`, `siteId`, `gatewayId`, `tenantId`
  - Por processo: `processId`, `processScript`
  - Por dispositivo: `deviceId`, `deviceType`, `driverType`, `driverMethod`

### Q8. O agrupamento automático dos erros faz sentido? Erros distintos estão sendo agrupados juntos?

**Resposta:** O agrupamento usa exclusivamente o algoritmo padrão do Sentry (baseado em stack trace + tipo da exceção).
**Pendência:** requer configuração no Sentry.

---

## Bloco 3 — Alertas e notificações
*(Configurações que residem exclusivamente no painel do Sentry — responsabilidade do Suporte.)*

### Q9. Somos notificados em cada novo evento ou existe algum limiar configurado?
*Alerta por volume (ex: 50 ocorrências em 10 min) reduz fadiga de alertas.*

**Resposta:** Reside exclusivamente no painel do Sentry. *(Pendência de configuração.)*

### Q10. Temos alerta de regressão configurado — alerta quando um erro resolvido volta a ocorrer?
*Um dos alertas mais valiosos para detectar problemas em novos deploys.*

**Resposta:** Reside exclusivamente no painel do Sentry. *(Pendência de configuração.)*

### Q11. Os alertas chegam para quem pode agir? Ou todos recebem tudo?

**Resposta:** Reside exclusivamente no painel do Sentry. *(Pendência de configuração.)*

---

## Bloco 4 — Processo de triagem e resolução

### Q12. Issues têm dono? Existe o hábito de atribuir erros a alguém? *(processo)*
*Sem responsável, erros ficam em aberto indefinidamente.*

### Q13. Usamos os status `Resolved`, `Ignored` e `In Progress`? Ou a lista cresce sem triagem? *(processo)*
*Uma lista sem triagem perde o sinal em dias — mesmo que haja erros críticos ali dentro.*

### Q14. Erros conhecidos e sem solução prevista são marcados como `Ignored` com prazo de revisão?
*Ignorar sem prazo vira acúmulo técnico invisível.*

**Resposta (consolidada para Q12–Q14):** Como o campo `release` não está configurado (Q6), o Sentry não tem capacidade de associar automaticamente quando um erro foi introduzido ou resolvido em um deploy específico, o que prejudica o workflow de resolução.
**Pendência:** uma vez que tenhamos releases estabilizadas, podem ser configuradas visões no Sentry para esse propósito.

---

## Bloco 5 — Visibilidade e dashboards

### Q15. Existe algum dashboard customizado ou o time usa apenas a lista padrão de issues? *(melhoria)*
*Um dashboard com top 10 erros por frequência já transforma a rotina de análise.*

### Q16. Conseguimos correlacionar picos de erros com deploys ou horários de carga? *(melhoria)*
*O Sentry tem gráfico de volume por tempo — vale usar junto com o histórico de releases.*

**Resposta (Q16):** Correlação com deploys prejudicada pela ausência do campo `release` (Q6). Sem esse campo, o gráfico de volume por tempo do Sentry não consegue marcar automaticamente os pontos de deploy.

---

## Leitura cruzada

- A dependência de `release` (Q6) é o nó central: bloqueia Q12–14 (workflow de resolução) e Q16 (correlação com deploys).
- Falta de política/filtro (Q1, Q3, Q4) tende a inflar o volume; o ruído de terceiros hoje depende só do CloudFlare.
- Blocos 3 (alertas) e parte do 2 (agrupamento, Q8) são responsabilidade do **Suporte** no painel do Sentry; os demais dependem de mudança nos produtos.
- Documento relacionado: `Auditoria_Configuracao_Sentry_Automind.md` (mesma pasta) — esta auditoria usa estas respostas como insumo.
