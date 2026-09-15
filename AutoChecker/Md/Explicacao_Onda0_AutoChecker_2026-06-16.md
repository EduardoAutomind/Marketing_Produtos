# Explicação da Onda 0 — AutoChecker

> **Para quem é este documento:** alguém que está começando na área de tecnologia e quer
> entender, sem jargão, o que é a "Onda 0" do plano de observabilidade do AutoChecker, o que
> cada etapa faz e em que pé ela está.
>
> | | |
> |---|---|
> | **Data** | 16/06/2026 |
> | **Produto** | AutoChecker (backend Django · worker Celery · frontend Next.js) |
> | **Ferramenta de monitoramento** | Sentry (org `automind-qd`) |
> | **Fonte de verdade do status** | Azure DevOps — org `automindautomacao`, projeto `AutoChecker` |
> | **Fontes lidas** | Cronograma (Excel 03/06), Auditoria Onda 0 (15/06), Azure DevOps ao vivo (16/06) |

---

## O que é a Onda 0?

Imagine que você vai construir uma casa de vários andares. Antes de levantar qualquer parede,
você precisa de uma **fundação firme e de um terreno limpo**. A Onda 0 é exatamente isso para o
plano de observabilidade do AutoChecker: é a **fase de saneamento da base**.

"Observabilidade" é a capacidade de **enxergar o que está acontecendo dentro do sistema** — saber
quando algo quebra, onde quebrou e por quê. A ferramenta que faz isso aqui é o **Sentry**, que
funciona como uma "central de alarmes" que captura os erros do programa.

O problema é que, hoje, essa central está com os alarmes **mal regulados**: dispara para coisas que
não importam, mistura erros de teste com erros de produção (clientes reais) e até deixa passar
informações pessoais que não deveriam aparecer. A Onda 0 conserta tudo isso **antes** de seguir em
frente.

Por isso ela é chamada de **"gate"** (portão): enquanto a Onda 0 não estiver concluída, as próximas
ondas (1 a 6) **não devem começar**. Não adianta construir andares novos sobre uma fundação torta.

A Onda 0 tem **8 etapas**. Abaixo, cada uma é explicada em linguagem do dia a dia.

---

## Etapa 1 — Padronizar a etiqueta `environment` e separar testes de produção

### O que é essa etapa?
Todo erro que chega ao Sentry vem com uma **etiqueta** dizendo de onde ele veio: do ambiente de
**produção** (onde estão os clientes reais), de **teste** ou da **máquina do próprio desenvolvedor**.
Hoje essas etiquetas estão bagunçadas — em especial no frontend (a tela que o usuário vê), onde a
maioria dos erros aparece marcada como "development" mesmo vindo de produção. É como receber uma
encomenda sem saber se o endereço é da loja ou da sua casa. Esta etapa garante que cada erro venha
com o ambiente certo.

### Onde ela atua no código?
Nos três "motores" do sistema, no ponto em que cada um liga o Sentry:
- **Backend** (servidor Django): `backend/config/settings/base.py:730`
- **Worker** (Celery — as tarefas automáticas que rodam em segundo plano): `worker/config/celery.py:24`
- **Frontend** (Next.js — o que o usuário vê): `instrumentation-client.ts:9`, `sentry.server.config.ts:9`, `sentry.edge.config.ts:10`

### O que ela afeta na prática?
Afeta a **confiança em tudo que vem depois**. Se erros de teste e de produção ficam misturados,
ninguém sabe se um alarme é grave (cliente afetado) ou inofensivo (alguém testando). Arrumar isso é
o que permite confiar nos números e nos alertas mais tarde.

### Status no Azure DevOps
🔍 **Pendente de confirmação.** Existem tarefas genéricas de "implementar método de observabilidade"
já concluídas (IDs `44192`, `44193`, `46787` — todas *Done*) e a inclusão do Sentry nos serviços
(`48860`, *Done*). Mas **nenhum item trata especificamente** da etiqueta `environment` ou da
configuração que falta no frontend. Ou seja: não há como confirmar pelo Azure que esta etapa
específica foi feita.

### Observação extra
O cronograma (a planilha) marca esta etapa como **"Concluído"**, mas isso se refere ao **código**, que
de fato já lê a etiqueta. O que ainda não está garantido é que o **deploy** (a publicação em produção)
preencha sempre a etiqueta certa. Quando a configuração falta, o sistema "chuta" o valor
`development` — e é justamente esse chute que polui o Sentry. Por isso a auditoria não considera a
etapa fechada.

---

## Etapa 2 — Padronizar a "versão" (release) e apontar o commit culpado

### O que é essa etapa?
Sempre que o sistema é publicado, ele ganha um número de **versão** (chamado de *release*). Quando um
erro acontece, é muito útil saber **em qual versão** ele surgiu — e, melhor ainda, **qual alteração de
código** provavelmente o causou (isso se chama *suspect commits*, o "commit suspeito"). Hoje isso não
está configurado, e pior: o frontend está mandando seus dados para um **projeto de teste errado** no
Sentry. É como enviar o relatório de vendas para o e-mail errado.

### Onde ela atua no código?
No frontend, no arquivo de configuração `next.config.js` (existem **duas cópias** dele:
`AutoChecker_Frontend/next.config.js` e `AutoChecker/frontend/next.config.js`). Em ambos, o destino
está apontado para `org: "automind-teste"` e `project: "javascript-nextjs"` — endereços de teste, não
os de produção. Também envolve as **pipelines do Azure** (as esteiras automáticas de publicação).

### O que ela afeta na prática?
Afeta a **velocidade para achar a causa de um problema**. Com a versão e o commit suspeito
configurados, quando algo quebra o time descobre em minutos qual mudança causou. Sem isso, vira
investigação no escuro. E os dados indo para o projeto errado significam que parte da informação
simplesmente **se perde**.

### Status no Azure DevOps
⚠️ **Parcial / Ambígua.** Existe apenas um item relacionado: a Task `36445` ("Configuração do pipeline
de releases no Azure DevOps"), que está em **"To Do"** (não iniciada) desde **maio de 2025** e **sem
responsável** — confirmado ao vivo em 16/06. Não há nenhum item sobre o commit suspeito (`set-commits`)
nem sobre o projeto errado do frontend.

### Observação extra
O cronograma marca esta etapa como **"Em andamento"**, mas no Azure ela aparece praticamente parada
há mais de um ano. Ter **duas cópias** do mesmo arquivo de configuração é um risco por si só: dá para
publicar a partir da pasta errada sem perceber.

---

## Etapa 3 — Remover a tarefa "fantasma" do agendador

### O que é essa etapa?
O sistema tem um **agendador de tarefas** (o "Celery Beat"), que é como um despertador que dispara
rotinas automáticas em horários certos. Existe uma tarefa que foi **removida do código**, mas o
despertador ainda guardou a "lembrança" dela e tenta executá-la. Como ela não existe mais, dá erro
toda vez — gerava por volta de **1.500 erros** repetidos. Esta etapa apaga essa "tarefa fantasma".

### Onde ela atua no código?
No worker (Celery): a lista oficial de tarefas agendadas fica em `worker/config/celery.py:69` e já
está correta. O problema está na **memória persistida do agendador**, num arquivo
(`/tmp/celerybeat-schedule`) que guarda a lembrança antiga. A tarefa em si
(`process_scheduled_notifications`) já está comentada/desativada no código.

### O que ela afeta na prática?
Afeta a **limpeza do painel**. Esse era um dos maiores geradores de "barulho" no Sentry: milhares de
erros repetidos que não significavam nada de novo, mas escondiam os problemas de verdade no meio da
poluição.

### Status no Azure DevOps
⚠️ **Parcial / Ambígua.** O núcleo do problema foi tratado: a Bug `53659` ("Limpar beat_schedule e
resetar celerybeat-schedule em prod") está **"Done"** (confirmado ao vivo). Porém ainda há pontas
soltas: a Task `53660` (uma duplicata da mesma coisa) ficou em **"To Do"**, e a `53707` ("Limpeza
preventiva no deploy") também está **"To Do"**.

### Observação extra
Sem a parte preventiva (`53707`), a "tarefa fantasma" pode **voltar a aparecer** num próximo deploy,
porque a limpeza foi feita à mão durante um incidente, e não automatizada. É como varrer o chão sem
consertar o vazamento que suja de novo.

---

## Etapa 4 — Corrigir as atualizações de banco que faltam para alguns clientes

### O que é essa etapa?
O AutoChecker atende vários clientes, e cada um tem seu próprio "compartimento" no banco de dados
(isso se chama *multi-tenant* — vários inquilinos no mesmo prédio). Quando o sistema é atualizado, ele
precisa aplicar as mudanças do banco **em todos os compartimentos**. Hoje a publicação aplica só no
"compartimento principal" e **esquece os dos clientes já existentes**. Resultado: o sistema procura
uma "gaveta" (tabela) que nunca foi criada para aquele cliente e dá erro do tipo *"relation does not
exist"*.

### Onde ela atua no código?
No processo de publicação (deploy) do worker: `backend/scripts/deploy.sh:97` e
`backend.azure-pipelines.yml:148/157` rodam só o comando `migrate` simples. O comando que aplica em
todos os compartimentos (`migrate_schemas`) só é usado quando um cliente **novo** é criado
(`backend/apps/tenants/signals.py:12`), nunca na atualização geral.

### O que ela afeta na prática?
Afeta **diretamente o cliente**: funções podem quebrar para quem está com o banco desatualizado. E
gera um volume grande de erros (no Sentry ao vivo, um único caso tinha mais de **540 ocorrências**).
São falhas reais, não barulho.

### Status no Azure DevOps
⚠️ **Parcial / Ambígua.** Existe a Task `51820` registrando o **sintoma** exato (`relation
"upload_document" does not exist`), em **"To Do"** (confirmado ao vivo). Há também tarefas antigas de
2025 sobre migração de schema (`35848` em *To Do*; `35829` foi **removida**). Mas **não existe item
para a correção de fundo** — adicionar o `migrate_schemas` ao deploy. Só os sintomas foram anotados,
não a causa.

### Observação extra
Enquanto a causa-raiz não tiver um item e uma correção, esses erros vão **continuar reaparecendo** a
cada nova atualização. Tratar sintoma sem tratar a causa é enxugar gelo.

---

## Etapa 5 — Unificar a "ligação" do Sentry e ativar a captura das tarefas automáticas

### O que é essa etapa?
Cada motor do sistema "liga" o Sentry de um jeito próprio, e essas formas estão **diferentes umas das
outras**. Existe um "manual padrão" pronto (uma função chamada `init_sentry`) que deixaria todos
iguais, mas **ninguém o usa**. Além disso, o backend não está capturando direito os erros das
**tarefas automáticas** (Celery), porque falta ativar um pedaço chamado `CeleryIntegration`. Esta
etapa padroniza a ligação e garante que esses erros sejam capturados.

### Onde ela atua no código?
- Backend liga "na mão" em `backend/config/settings/base.py:728-736` (sem a integração do Celery).
- Worker liga "na mão" em `worker/config/celery.py:22-32`.
- O manual padrão pronto está em `shared/observability/sentry.py` — e é **chamado apenas nos testes**,
  nunca em produção.

### O que ela afeta na prática?
Afeta a **cobertura do monitoramento**. Sem a integração do Celery no backend, certos erros das
tarefas automáticas podem **passar despercebidos** ou aparecer mal agrupados — ou seja, problemas
acontecendo sem que ninguém veja.

### Status no Azure DevOps
❌ **Não mapeada.** A busca por `init_sentry` e `CeleryIntegration` (no título e na descrição dos itens)
retornou **zero** resultados. Não existe nenhum work item para esta etapa.

### Observação extra
É uma das duas etapas **sem nenhum rastreamento** no Azure. O esforço é considerado **pequeno (P)**, ou
seja, é uma correção relativamente barata — mas que hoje nem sequer existe como tarefa registrada.
Atenção a um detalhe técnico: só mudar quem chama o manual **não basta**; o próprio manual precisa ser
ajustado para dar a integração do Celery ao backend.

---

## Etapa 6 — Filtrar o "barulho" e consertar o filtro de health quebrado

### O que é essa etapa?
Boa parte dos erros no Sentry não são problemas de verdade. São **robôs de varredura** da internet
batendo na porta do sistema (`DisallowedHost`), tentativas de acesso esperadas que falham (login,
token) e um filtro **quebrado** que deveria ignorar as verificações de saúde do sistema, mas que está
apontando para o endereço errado. Esta etapa silencia o que é barulho — **sem** silenciar o que é
incidente real.

### Onde ela atua no código?
No backend, no ponto que decide o que mandar (ou não) para o Sentry: `backend/config/settings/base.py:716`.
Ali o filtro procura pelo endereço `/health/`, mas o endereço real da verificação de saúde é
`/api/core/healthcheck/` (definido em `apps/core/urls.py:12`). Como os textos não batem, o **filtro
nunca funciona** — está "morto".

### O que ela afeta na prática?
Afeta a **capacidade de enxergar o que importa**. Com o painel cheio de barulho, os problemas reais
ficam escondidos e o time perde tempo (e confiança nos alertas). Atenção: a parte de login/token
**não** deve ser silenciada em bloco — ali existem incidentes verdadeiros que precisam ser
classificados caso a caso.

### Status no Azure DevOps
⚠️ **Parcial / Ambígua.** Uma fatia do barulho foi atacada na origem: a Bug `53661` (validar dados no
middleware) está **"Done"**. Mas **não há item** para configurar o filtro de barulho (`before_send`),
nem para o `DisallowedHost`, nem para corrigir o filtro de health quebrado. Os itens de healthcheck
encontrados (`53684`, `53997`) **criam endpoints novos** — não consertam o filtro do Sentry.

### Observação extra
Mesmo com a `53661` concluída, o **barulho dominante continua**, porque o cerne da etapa (os filtros)
segue sem tarefa. Esta etapa cruza com a Etapa 8 (triagem): limpar o barulho aqui facilita muito a
triagem lá.

---

## Etapa 7 — Proteger dados pessoais (LGPD) no frontend

### O que é essa etapa?
Quando um erro acontece, o Sentry pode capturar um "retrato" do que estava na tela e dados do usuário.
Hoje o frontend está configurado para **enviar dados pessoais** (a opção `sendDefaultPii` está ligada),
manda o **e-mail do usuário** junto com os erros, e grava **vídeos da sessão** (Session Replay) **sem
borrar** telas sensíveis — como **CNH, ASO e CPF**. Esta etapa desliga esse vazamento e aplica
mascaramento.

### Onde ela atua no código?
No frontend: a opção `sendDefaultPii: true` aparece em `instrumentation-client.ts:21`,
`sentry.server.config.ts:16` e `sentry.edge.config.ts:17`. O envio do e-mail está em
`modules/auth/hooks/useAuth.tsx:175`. A gravação de sessão sem mascaramento está em
`instrumentation-client.ts:18-19`.

### O que ela afeta na prática?
Afeta **conformidade legal (LGPD) e privacidade dos clientes**. Documentos pessoais e e-mails podem
estar sendo gravados e guardados num sistema externo. Este é um **risco jurídico real**, não apenas
técnico.

### Status no Azure DevOps
❌ **Não mapeada.** A busca por termos de proteção de dados (`sendDefaultPii`, `scrubbing`, `PII`)
ligados ao Sentry retornou **nenhum item**. Os itens de LGPD que existem (`55050`, `55088`) são de
**produto** (aceite de termos, central de ajuda do cliente) e **não** tratam de mascarar dados no
Sentry.

### Observação extra
**É a etapa mais sensível da Onda 0.** Tem risco legal e está **completamente sem rastreamento**. A
recomendação da auditoria é tratá-la com **urgência**: desligar o envio de dados pessoais, parar de
mandar o e-mail e borrar as telas sensíveis nas gravações.

---

## Etapa 8 — Fazer a faxina (triagem) do backlog de erros

### O que é essa etapa?
"Triagem" é como a fila de emergência de um hospital: olhar cada caso e classificar — **resolvido**,
**ignorar** (com prazo), **em andamento** ou **aguardando**. Hoje há por volta de **152 erros em
aberto** no Sentry e **zero foram resolvidos nos últimos 30 dias**. É uma caixa de entrada que ninguém
está esvaziando. Esta etapa coloca a casa em ordem.

### Onde ela atua no código?
Esta etapa **não mexe no código** — é trabalho de organização feito **dentro do painel do Sentry**
(classificar issues, definir critérios, atribuir donos). Cruza com várias outras etapas, porque
resolver as causas (Etapas 3, 4, 6) é o que faz a fila diminuir.

### O que ela afeta na prática?
Afeta a **rotina de cuidado com o sistema**. Sem triagem, o painel só cresce e perde utilidade. Com
triagem, o time passa a tratar os erros de forma contínua, em vez de só apagar incêndios.

### Status no Azure DevOps
🔄 **Em andamento.** Existe esforço ativo: dois itens "guarda-chuva" — a Bug `53700` ("Estabilização de
Issues Sentry — Maio/2026") e a Bug `51817` ("Sentry Erros"). Mas ambos estão em **"New"** (confirmado
ao vivo), poucos filhos foram concluídos (ex.: `51818`, *Done*) e a maioria segue em **"To Do"**. É uma
triagem **parcial e reativa**, não a faxina completa que a etapa pede.

### Observação extra
O fato mais importante foi confirmado ao vivo: **nenhuma issue do AutoChecker foi resolvida** (as
poucas resolvidas na organização são de outro produto). A triagem, na prática, ainda não começou de
verdade.

---

## Resumo geral da Onda 0

| # | Nome da etapa | Status no Azure DevOps | Risco principal |
|---|---|---|---|
| 1 | Etiqueta `environment` + separar teste/produção | 🔍 Pendente de confirmação (só itens genéricos *Done*) | Frontend reportando como "development" em produção |
| 2 | Release + commit suspeito + pipelines | ⚠️ Parcial (`36445` *To Do* desde 2025, sem dono) | Dados indo para o projeto de teste errado |
| 3 | Remover tarefa fantasma do agendador | ⚠️ Parcial (`53659` *Done*; `53660`/`53707` *To Do*) | A tarefa fantasma pode voltar num próximo deploy |
| 4 | Atualizações de banco que faltam (clientes) | ⚠️ Parcial (só sintoma `51820` *To Do*) | Erros reais para clientes continuarão surgindo |
| 5 | Unificar ligação do Sentry + Celery | ❌ Não mapeada (zero itens) | Erros de tarefas automáticas não capturados |
| 6 | Filtrar barulho + consertar filtro de health | ⚠️ Parcial (`53661` *Done*; filtros sem item) | Barulho dominante continua escondendo o que importa |
| 7 | Proteger dados pessoais (LGPD) no frontend | ❌ Não mapeada (zero itens) | **Risco legal:** CNH/ASO/CPF e e-mail expostos |
| 8 | Faxina (triagem) do backlog de erros | 🔄 Em andamento (guarda-chuvas `53700`/`51817` *New*) | Triagem não fechada; 0 erros resolvidos |

**Contagem por situação (segundo o Azure DevOps, validado em 16/06):**
- ✅ Concluídas (item *Done* cobrindo a etapa): **0**
- 🔄 Em andamento: **1** (Etapa 8)
- ⚠️ Parciais / ambíguas: **4** (Etapas 2, 3, 4, 6)
- 🔍 Pendente de confirmação: **1** (Etapa 1)
- ❌ Sem nenhum rastreamento: **2** (Etapas 5 e 7)

---

## Conclusão

**A Onda 0 NÃO pode ser considerada concluída, e o gate deve permanecer FECHADO.**

A regra é clara: uma etapa só conta como pronta quando existe um item no Azure DevOps em estado
**"Done"** cobrindo o que ela pede. Pelo que o Azure mostra hoje (16/06/2026, validado ao vivo),
**nenhuma das 8 etapas atende a essa condição**. Existem itens *Done* avulsos (como `53659`, `53661` e
`51818`), mas eles resolvem pedaços, não o escopo inteiro de nenhuma etapa.

Mais do que "faltar concluir", o problema de fundo é de **rastreabilidade**: as 8 etapas da Onda 0
praticamente **não existem como tarefas dedicadas** no Azure Boards. O que há é trabalho genérico de
observabilidade e correções pontuais e reativas de erros. Sem itens claros, etapa por etapa, não há
como provar conclusão — e duas etapas críticas (a **5**, técnica, e a **7**, de risco legal/LGPD) não
têm absolutamente nenhum item.

**Recomendação:** antes de tentar avançar, criar no Azure os 8 itens rastreáveis (quebrando a Feature
`40531` "Observabilidade"), tratar com urgência a Etapa 7 (dados pessoais) e fechar de fato a triagem
da Etapa 8.

---

### Balanço final

- **Etapas com algum work item relacionado no Azure DevOps:** **6** (Etapas 1, 2, 3, 4, 6 e 8) — mas
  nenhuma com item *Done* cobrindo todo o escopo, e a Etapa 1 só tem itens genéricos.
- **Etapas sem nenhum rastreamento:** **2** (Etapas 5 e 7).
- **Etapas efetivamente concluídas (item *Done* de escopo compatível):** **0**.
- **O gate da Onda 0 pode ser liberado?** **NÃO.** O portão permanece fechado.

---

*Documento explicativo gerado em 16/06/2026. Fontes: Cronograma (`Cronograma_Observabilidade_AutoChecker_2026-06-03.xlsx`),
Auditoria (`Auditoria_Onda0_AutoChecker_2026-06-15.md`) e consulta ao vivo ao Azure DevOps
(org `automindautomacao`, projeto `AutoChecker`) em 16/06/2026. Todos os status de conclusão vêm do
Azure DevOps; onde não há item, está registrado explicitamente.*
