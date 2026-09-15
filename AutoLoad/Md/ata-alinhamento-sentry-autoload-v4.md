# ATA DE REUNIÃO
## Alinhamento Sentry vs AutoLoad V4

| Campo         | Valor              |
| ------------- | ------------------ |
| Data          | 22 de maio de 2026 |
| Horário       | 10h30 – 11h00      |
| Local         | Microsoft Teams    |
| Duração       | 30 minutos         |
| Facilitador   | Eduardo Santos     |
| Redator       | Raian Almeida      |
| Classificação | Uso interno        |

## PARTICIPANTES

| Nome                             | Cargo / Função                                               |
| -------------------------------- | ------------------------------------------------------------ |
| Eduardo Santos                   | Organizador                                                  |
| Paulo Eduardo Martins Sacramento | Desenvolvimento — responsável pela frente de observabilidade |
| Fábio dos Santos Daniel          | Suporte / Implantação                                        |
| Raian Almeida                    | Produto                                                      |

## PAUTA DA REUNIÃO

1. Diagnóstico do estado atual do Sentry para suporte e troubleshooting do AutoLoad V4
2. 16 perguntas elaboradas por Fábio dos Santos Daniel, agrupadas em 5 temas
3. Alinhamento sobre observabilidade do AutoChecker

## CONTEXTO E MOTIVAÇÃO

Fábio dos Santos Daniel compartilhou tela com os questionamentos preparados. Ponto de partida: o V3 (VK) possui estrutura onde os logs de cada componente ficam em pastas específicas. Quando um componente para, a primeira fonte de dados é aquela pasta. No V4 essa referência não existe da mesma forma, e o Sentry é o substituto natural — mas ainda sem organização.
- Cenário concreto: analista recebe chamado "AutoLoad não está se comunicando, não conseguem fazer carregamento". Hoje, no V4, não há caminho organizado para buscar logs no Sentry.

## TEMA 1 — O QUE ESTÁ SENDO ENVIADO AO SENTRY?

P1 — Critério atual de envio / política definida
Não há política formal. Risco clássico: enviar tudo sem triagem, o que inviabiliza a análise.
P2 — Erros não tratados vs. exceções capturadas manualmente
Fábio relatou caso da véspera: cliente pediu alerta quando leitura de preset ficasse fora. Orientação: cuidado com intermitência — rede indo e voltando geraria avalanche de chamados.
- Válido para chamado: integração V4 com ERP/SAP não está funcionando.
- Falso positivo — não abrir chamado: leitura intermitente de equipamento de campo por problema de rede industrial do cliente.
P3 — Logs de nível info ou debug em produção
- Info: identifica o estado do sistema ("preset está OK", "integração está OK"). Precisa existir primeiro.
- Debug: "cereja do bolo" — permite saber, por exemplo, que o firmware do preset foi atualizado e o driver não está preparado.
Caso Ultracargo: time levou aproximadamente 1 mês/HH para descobrir que o POST de um equipamento de campo estava queimado. Com debug estruturado no Sentry, Ian teria identificado a mudança de firmware em minutos. Debug ainda sem maturidade para implantação — sequência correta: primeiro info, depois debug.
P4 — Erros esperados ou de terceiros
Terceiros = ferramentas externas administradas pelo próprio cliente (ex: IFIX na Ultracargo). Redes industriais frequentemente segregadas da TI — fonte de telemetria pode passar por gateway intermediário, gerando erros que não são bugs do produto.

## TEMA 2 — ORGANIZAÇÃO E CONTEXTO DOS EVENTOS

P5 — Environments configurados
Fábio confirmou satisfeito: produção, staging e desenvolvimento já estão separados.
P6 — Campo release por evento
No V4 todos os clientes devem ter a mesma versão — sem personalizações por cliente (exceto mudança de negócio). Permite correlacionar comportamento do sistema com a versão em uso.
- Paulo Eduardo: já implementou identificação de releases e deploys no dashboard do Sentry.
P7 — Tags customizadas
Principal recurso para filtrar eventos por contexto de negócio. Sem tags, a análise por processo é impossível.
P8 — Agrupamento automático dos erros
Necessidade de definir se o agrupamento será automático (Sentry nativo) ou customizado por contexto de negócio.

## TEMA 3 — ALERTAS E NOTIFICAÇÕES

P9 — Threshold / ciclo de notificação
Time de suporte não está pronto para receber notificações brutas do Sentry. O V4 é refém da infraestrutura do cliente: evento intermitente abre chamado desnecessário. Hoje o fluxo é: cliente percebe o problema → abre ticket (5 a 10 min) → passa para o time. Fábio propõe definir um ciclo de notificação antes de disparar alerta.
Ponto adicional — Rastreabilidade de mudanças de processo feitas pelo cliente
Risco específico do V4 inexistente no V3: o cliente pode alterar etapas do processo diretamente no sistema. Exemplo: Ultracargo colocou a balança antes do carregamento. Resultado: operação que demorava segundos passou a demorar 20 minutos. Analista de suporte não consegue identificar a causa sem rastrear a mudança de configuração.
- Necessidade: mecanismo para identificar alterações de processo feitas pelo cliente e correlacionar com impacto no resultado final. Fábio classificou como "vital e cereja do bolo para o V4".
P10 — Alerta de regressão
Classificado como evolutivo pelo Fábio — não prioritário no momento atual.
P11 — Alertas chegam para quem pode agir
Necessidade de definir responsáveis por nível (N1/N2/N3) antes de ativar qualquer política de alertas.

## TEMA 4 — PROCESSO DE TRIAGEM E RESOLUÇÃO

P12 — Issues têm dono / atribuição de erros
Fábio descreveu o cenário: analista N1 chega ao limite do entendimento e precisa saber para quem atribuir o issue dentro do V4. Raian confirmou que haverá estrutura N1/N2/N3.
- N1: suporte — chamados básicos e intermediários.
- N3: produto/desenvolvimento — quando N1 esgota o entendimento.
P13 e P14 — Status Resolved / Ignored / In Progress
Necessidade de definir processo formal de triagem, com envolvimento de Paulo Eduardo e Gustavo.

## TEMA 5 — VISIBILIDADE E DASHBOARDS

P15 — Dashboard customizado
Fábio descreveu a visão: dashboard do V4 com gateway e elementos de campo, exibindo conectividade por cliente (semáforo verde/amarelo). Time de suporte tem televisão interna — dashboard seria exibido permanentemente. Objetivo: resposta tática rápida sem depender de ticket do cliente.
P16 — Correlação de picos com deploys
Evolutivo/futuro: top 5 incidentes recorrentes → identificar padrão → mitigar na estrutura do cliente. Fábio classificou como "evolução do produto".

## VISÃO DE PRODUTO E AUTOCHECKER

Dashboard unificado — Raian
Raian apresentou estado atual: dashboard unificado em construção no Sentry para AutoLoad V4, Automed e AutoChecker. Objetivo: classificar erros pela etapa do processo, não por módulo técnico.
AutoChecker
AutoChecker já está em produção (integrado com V3) e ainda não possui observabilidade configurada. Fábio solicitou urgência: documentação técnica e capacitação do time de suporte em paralelo ao AutoLoad V4.
- Jakiam: responsável pela configuração do AutoChecker no sistema de suporte (faturamento de atendimento por cliente).

## DECISÕES

- D1: O time de Produtos irá elaborar o dashboard de observabilidade padronizado para os produtos AutoLoad Cloud, AutoChecker e Automed e disponibilizar para o time de Suporte.
- D2: O dashboard Sentry será unificado por produto, com classificação de eventos por etapa de processo — não por módulo técnico.
- D3: AutoChecker entra na mesma fila de observabilidade que o AutoLoad V4 — setup em paralelo e com urgência.
- D4: A política de alertas só será ativada após definição do ciclo de notificação e supressão de falsos positivos de infraestrutura de campo.
- D5: Sequência de maturidade de logging: primeiro nível info (estado do sistema), depois nível debug (diagnóstico de campo). Não há maturidade para debug ainda.
- D6: Chamados não devem ser abertos para eventos de campo com falso positivo (equipamento, rede industrial). Chamados são válidos para problemas de processo (ex: integração ERP).

## RESUMO DE AÇÕES

| #   | Ação                                                                                                                                 | Responsável       | Esforço |
| --- | ------------------------------------------------------------------------------------------------------------------------------------ | ----------------- | ------- |
| 1   | Criar cronograma de observabilidade por produto (AutoLoad V4, Automed, AutoChecker) com marcos de entrega                            | Paulo Eduardo     | M       |
| 2   | Contatar Jakiam para configurar o AutoChecker no sistema de suporte (faturamento de atendimento por cliente)                         | Fábio             | P       |
| 3   | Solicitar ao Milton a documentação técnica do AutoChecker para subsidiar o setup de observabilidade e capacitação do time de suporte | Raian             | P       |
| 4   | Definir os níveis N1/N2/N3 de atendimento para AutoLoad V4 e mapear os responsáveis em cada nível                                    | Produto + Suporte | M       |

## OBSERVAÇÕES FINAIS

A transcrição do Teams apresentou ruídos de áudio significativos na fala de Paulo Eduardo — sua participação foi principalmente confirmações e comentários breves; o conteúdo substantivo veio de Fábio e Raian. As 16 perguntas elaboradas pelo Fábio não foram respondidas nesta reunião — o alinhamento foi sobre estado atual, diagnóstico e direcionamento. O item sobre rastreabilidade de mudanças de processo feitas pelo cliente (Tema 3) é um risco específico do V4 sem precedente no V3.

Documento gerado a partir de transcrição automática — sujeito a revisão dos participantes.

---
*Ata gerada automaticamente a partir de transcrição.*