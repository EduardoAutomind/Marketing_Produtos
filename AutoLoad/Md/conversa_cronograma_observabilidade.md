# Conversa — Cronograma de Implantação de Observabilidade

**Produtos:** AutoLoad Cloud, AutoChecker, Automed
**Ferramenta central:** Sentry
**Interlocutor:** Raian

---

## Pergunta inicial

> Preciso montar um cronograma de implantação de observabilidade para os produtos AutoLoad Cloud, AutoChecker e Automed. Para isso, preciso primeiro entender quais as principais entregas de um bom sistema de observabilidade (considerando que vamos usar a ferramenta Sentry) e como podemos definir um cronograma com marcos e entregas parciais que já entreguem valor ao longo da implementação.

---

## Resposta — 22 de mai.

Boa, Raian. Vamos estruturar isso em duas camadas: primeiro o que define um bom sistema de observabilidade (com Sentry no centro), depois como transformar isso num cronograma com marcos incrementais que entregam valor desde cedo.

Antes de detalhar, deixa eu confirmar uma coisa sobre o estado atual para não te entregar um cronograma genérico:

Enquanto você responde, deixa eu já adiantar o conteúdo conceitual — ele vale independente das suas respostas, e aí ajustamos o cronograma com base no que você escolher.

### As entregas de um bom sistema de observabilidade

Observabilidade não é "instalar uma ferramenta". São camadas de capacidade que respondem a perguntas progressivamente mais difíceis sobre o sistema. Vou organizar pelo que cada camada te entrega, mapeando o que o Sentry cobre nativamente e onde ele tem limite.

#### 1. Captura de erros e exceções (a base)

É onde o Sentry brilha e por onde todo mundo começa. Captura automática de exceções não tratadas no Django (backend) e no Next.js (frontend e SSR), com stack trace completo, contexto da requisição, breadcrumbs e agrupamento inteligente de erros similares.

**A pergunta que responde:** "o que quebrou, onde, e quantos clientes foram afetados?".

Para o seu caso de N1/N2, isso já ataca diretamente o problema de descobrir o erro só quando o cliente liga.

#### 2. Performance / tracing (APM)

Rastreamento de transações: quais endpoints estão lentos, quais queries no PostgreSQL estão pesando, onde está o gargalo numa requisição que passa por Django → banco → integração externa. O tracing distribuído é especialmente valioso no seu contexto porque **43,6% dos seus tickets do AutoLoad V3 vinham de dependência de terceiros** — com spans você consegue provar que a lentidão está na chamada ao sistema do fornecedor, não no seu código.

**Responde:** "por que está lento e de quem é a culpa?".

#### 3. Logs estruturados e correlacionados

O Sentry hoje cobre logs (você já confirmou isso na sua análise anterior), e o ganho real não é só armazenar log — é correlacionar o log com o erro e a transação. Quando um erro aparece, você vê os logs daquela mesma requisição, com o mesmo `trace_id`.

**Responde:** "o que aconteceu nos segundos antes do problema?".

#### 4. Métricas de negócio

Aqui sai do técnico e entra no que importa para o cliente: volume de carregamentos processados, documentos validados no AutoChecker, medições submetidas no AutoMed, taxa de sucesso de submissão à ANP/DPP. Você confirmou que o Sentry cobre métricas de negócio. Isso é o que vira dashboard para liderança e base para SLA.

**Responde:** "o produto está entregando o resultado esperado para o cliente?".

#### 5. Alertas e workflows de resposta

De nada adianta capturar tudo se ninguém é avisado. Regras de alerta (taxa de erro acima do normal, novo tipo de erro, degradação de performance, queda em métrica de negócio), roteamento para o time certo, integração com Teams/e-mail.

**Responde:** "como eu sei do problema antes do cliente?".

#### 6. Health checks e disponibilidade (uptime)

Monitoramento de que o serviço está de pé — cron monitoring para jobs agendados (relevante para submissões periódicas à ANP), uptime checks.

**Responde:** "o serviço está no ar e os jobs rodaram?".

#### Observação importante de escopo

Pela sua própria análise anterior, o **Prometheus continua necessário** para métricas de infraestrutura (CPU/memória/disco dos containers no Easypanel/VPS). O Sentry não cobre bem essa camada. Então o "sistema de observabilidade completo" tem **Sentry como espinha dorsal de aplicação+negócio**, e **Prometheus como complemento de infra**. Vale decidir desde já se infra entra neste cronograma ou fica numa trilha separada.

### A lógica do cronograma incremental

O princípio para entregar valor cedo é: cada onda deve deixar o produto observável o suficiente para um caso de uso real antes de seguir para a próxima camada. A sequência que maximiza valor early:

A primeira entrega de valor é só a **camada 1 (captura de erros) rodando em produção** — mesmo sem nada mais, você já sai do escuro. Em poucos dias de configuração você já recebe erros reais que hoje só descobre por ticket. Esse é o marco que "paga" o projeto sozinho. As camadas seguintes (performance, métricas de negócio, alertas) são incrementos que aumentam a profundidade, mas a base já está gerando retorno.

Por isso eu sugiro estruturar em marcos onde cada um corresponde a uma camada madura em produção, e **não fatiar por produto isoladamente** — você instala a camada 1 nos três e só depois sobe para a camada 2, ou faz um produto-piloto completo e replica. Sua resposta sobre "juntos ou em ondas" decide exatamente isso, e é a decisão arquitetural mais importante do cronograma.

Assim que você marcar as três perguntas acima, eu monto o cronograma concreto com marcos, datas relativas (sprints/semanas), entregas parciais e critério de "pronto" de cada marco. E aí entra a decisão de formato: para um cronograma de implantação com marcos e dependências, minha recomendação é **PPTX** (board de status/roadmap visual para apresentar à liderança e ao time) ou **XLSX** (se você quer algo operacional, com colunas de responsável, esforço, status e datas, que dê pra atualizar semanalmente como você já faz com os relatórios de produtividade).

Qual dos dois formatos faz mais sentido para como você vai usar esse cronograma — apresentar/comunicar (PPTX) ou operar/acompanhar (XLSX)? E me confirma as três escolhas acima que eu sigo.

---

## Perguntas e respostas

**P:** Qual o ponto de partida de observabilidade dos três produtos hoje?
**R:** Zero estruturado (só logs soltos / acesso ao servidor)

**P:** Qual o objetivo prioritário desta implantação?
**R:** Classificação:
1. Antecipar problemas antes do cliente reportar
2. Reduzir MTTR / resolver incidentes mais rápido
3. Visibilidade para liderança / SLAs com clientes
4. Reduzir dependência de fornecedor terceiro

**P:** Os três produtos entram juntos ou em ondas?
**R:** Tudo em paralelo

---

## Resposta — 22 de mai. (follow-up)

Perfeito, Raian. As três respostas mudam o desenho de forma importante, então deixa eu refletir o que elas implicam antes de propor o cronograma:

### Implicações das respostas

**Partindo do zero estruturado** → não dá pra pular a fundação. A primeira onda obrigatoriamente é setup de SDK + captura de erros, porque sem isso nada mais existe. A boa notícia é que do zero o ganho marginal da camada 1 é enorme — você sai do "descobrir por ticket" para "descobrir em tempo real" de uma vez.

**Prioridade #1 = antecipar antes do cliente reportar** → isso é revelador. O objetivo número um não é o erro em si (camada 1), é o **alerta proativo (camada 5)** e o **health check/uptime (camada 6)**. Ou seja, a captura de erros sozinha não atende seu objetivo principal — ela é pré-requisito, mas o valor que você quer só aparece quando o alerta dispara antes do telefone tocar. Isso me faz **antecipar a camada de alertas**: em vez de deixá-la para o fim, ela precisa entrar logo após a captura básica, ainda na primeira metade do cronograma. MTTR (sua #2) reforça isso — alerta rápido + contexto de log/trace é exatamente o que derruba o tempo de resolução.

**Tudo em paralelo nos três produtos** → aqui mora o maior risco do plano. Três produtos em paralelo do zero, com um time que tem André, Luis, Gustavo e Daniel divididos entre entregas do AutoLoad V4 e tudo mais, pode virar três implantações pela metade. A forma de proteger isso sem abrir mão do paralelismo é **padronizar a fundação**: criar uma vez um módulo/config de instrumentação Sentry reutilizável (um "observability starter" para Django e outro para Next.js) e aplicar nos três. Assim o paralelo não multiplica o trabalho de design por três, só o de aplicação. Vou embutir isso como o primeiro marco.

### Sequência de camadas ajustada à prioridade

Com isso, a sequência de camadas que atende sua ordem de prioridade fica:

1. **Fundação reutilizável**
2. **Captura de erros nos 3**
3. **Alertas + uptime/health** (sobe de posição por causa da sua #1)
4. **Logs correlacionados + tracing** (MTTR, #2)
5. **Métricas de negócio + dashboards de liderança** (#3)
6. **Endurecimento e dependência de terceiros** (#4, que se resolve com os spans de tracing já entregues na onda anterior)

### Decisão de formato pendente

Antes de eu montar o arquivo, só falta a decisão de formato. Como você ainda não me disse, e isso muda bastante o que eu produzo, deixa eu te dar a recomendação com justificativa:

Para um cronograma de implantação que você vai operar e atualizar semanalmente — com responsável por entrega, esforço, status colorido, datas de início/fim e dependências — minha recomendação é **XLSX**. É o formato que conversa com como você já trabalha (relatórios de produtividade a partir de CSV do Azure DevOps), permite filtro/ordenação por produto ou por onda, e é vivo: o time atualiza status sem você refazer nada. Um cronograma é por natureza uma ferramenta de acompanhamento, não um documento estático.

Se o uso principal for apresentar à liderança o plano e os marcos (sem precisar atualizar célula a célula), aí PPTX com um board de ondas/timeline visual seria melhor.

Minha sugestão é **XLSX** pelo caráter operacional do artefato. Confirma que sigo com XLSX, ou prefere PPTX (ou os dois — XLSX operacional + um slide-resumo para liderança)?
