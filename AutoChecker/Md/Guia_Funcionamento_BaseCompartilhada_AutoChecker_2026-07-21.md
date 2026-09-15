# Em uma frase

O **AutoChecker** recebe os documentos de motoristas e veículos de uma transportadora, **lê sozinho o que está escrito neles**, confere junto aos órgãos oficiais se são verdadeiros, avisa quando estão perto de vencer e repassa os dados já conferidos para o sistema de gestão do cliente.

O que hoje é feito com pasta, planilha e e-mail passa a acontecer sem ninguém digitar nada.

> 💡 Este guia foi escrito para o time de marketing. Ele explica **como o produto funciona de verdade**, com o que pode ser afirmado com segurança e o que deve ser evitado na comunicação. Todas as informações vêm da documentação oficial do produto (revisão de 21/07/2026).

---

# 1. O problema que o produto resolve

Uma transportadora precisa provar, a qualquer momento, que cada motorista e cada veículo em operação está com a documentação válida. São 17 tipos de documento diferentes — CNH, MOPP, ASO, CRLV, Cronotacógrafo, RNTRC, entre outros.

**Antes do AutoChecker**, isso vivia espalhado em pastas físicas, drives compartilhados e planilhas. A conferência era visual e manual. Documento vencido passava despercebido — e isso significa multa, apreensão do veículo e caminhão parado.

**Com o AutoChecker**, o documento é enviado uma vez e o sistema cuida do resto: lê, identifica, confere, valida, avisa e integra.

---

# 2. O que é a "Base Compartilhada"

O AutoChecker funciona como um **condomínio**.

Cada empresa cliente tem o seu próprio espaço dentro da plataforma. Os dados de uma empresa **não se misturam** com os de outra: documentos, motoristas, veículos, usuários e configurações ficam separados. Cada empresa define suas próprias regras, seus próprios usuários e seus próprios limites.

A **Base Compartilhada** é um desses espaços — com uma característica: em vez de atender uma única empresa, ela abriga **várias empresas convivendo no mesmo ambiente**. É o modelo usado quando um grupo, um operador logístico ou a própria AutoMind precisa acomodar vários clientes sob uma mesma estrutura, sem abrir um ambiente novo para cada um.

Na prática isso significa:

- **Onboarding mais rápido** — uma empresa nova entra sem precisar montar um ambiente do zero.
- **Custo diluído** — a estrutura é compartilhada entre os participantes.
- **Mesma experiência** — quem usa não percebe diferença; a tela e o fluxo são os mesmos.

> ⚠️ **Ponto de atenção para a comunicação:** a Base Compartilhada é um ambiente **multi-empresa**. Ao falar de "isolamento total de dados", o correto é dizer que **cada ambiente é isolado dos demais** — e não afirmar que cada empresa individual dentro da Base Compartilhada tem um ambiente próprio, porque não tem.

---

# 3. A jornada de um documento — os 6 passos

Este é o coração do produto. Quando alguém envia uma foto ou um PDF de um documento, ele percorre seis etapas, uma após a outra, sem intervenção humana.

### Passo 1 — Envio

O documento chega pelo site, pelo aplicativo ou por um link enviado ao motorista. Podem ser enviados até **10 arquivos por vez**, de até **20 MB cada**, nos formatos JPEG, PNG, TIFF ou PDF.

Se o mesmo arquivo já tiver sido enviado antes, o sistema reconhece e não duplica.

### Passo 2 — Leitura

O sistema **lê o texto do documento** usando tecnologia de reconhecimento óptico (a mesma família de tecnologia que digitaliza um livro). Ao final, ele atribui uma **nota de qualidade da leitura** — de "ilegível" a "ideal".

Essa nota é importante: um documento fotografado torto, escuro ou amassado gera uma leitura pior, e o sistema sabe disso e registra.

### Passo 3 — Identificação do tipo

Uma inteligência artificial olha o texto lido e responde: *"isto é uma CNH"*, *"isto é um CRLV"*, *"isto é um ASO"*.

**Ninguém precisa dizer ao sistema o que está enviando.** Se a IA concluir que o arquivo não é um documento válido para o processo, ele é marcado como inválido ali mesmo e o fluxo para.

### Passo 4 — Extração dos dados

Identificado o tipo, o sistema extrai os campos que interessam: CPF, nome, placa, chassi, categoria da habilitação, data de validade e assim por diante. Existe um extrator especializado para cada tipo de documento.

### Passo 5 — Conferência oficial

Aqui está o maior diferencial do produto. O sistema **consulta as fontes oficiais do governo** para confirmar que o documento é verdadeiro:

- **CNH e CRLV** são conferidos junto ao **SERPRO** (o órgão federal de processamento de dados), pela leitura do QR Code do próprio documento.
- **Outros certificados** — CIV, CIPP, CTPP, CVV, Cronotacógrafo, licenças do IBAMA — são conferidos consultando automaticamente os sites dos órgãos responsáveis.

O resultado dessa conferência é registrado com honestidade, e essa nuance é importante:

| Resultado | O que significa |
|---|---|
| **Autenticado** | O órgão oficial confirmou que o documento é verdadeiro |
| **Não autenticado** | Não foi possível conferir (por exemplo, o cliente não contratou este módulo) |
| **Inválido** | A fonte oficial confirmou que o documento **não** é válido |
| **Indisponível** | O site do órgão estava fora do ar naquele momento |
| **Inconclusivo** | A consulta falhou por questões técnicas |

> ⚠️ **"Inconclusivo" não é "falso".** O produto foi desenhado deliberadamente para não acusar um documento de fraude quando na verdade apenas não conseguiu consultar. Esse cuidado é um argumento de venda — mostra maturidade e responsabilidade.

### Passo 6 — Integração

Com o documento lido, identificado e conferido, o sistema **envia automaticamente os dados para o sistema de gestão do cliente** — o ERP, o TMS ou o sistema de frota que a empresa já usa.

Só que existe uma trava inteligente: o envio só acontece **quando todos os documentos obrigatórios daquele motorista ou veículo estão em ordem**. O sistema não empurra dado incompleto para o sistema do cliente.

---

# 4. Motorista + veículo: o conceito de "composição"

O AutoChecker não avalia documentos soltos. Ele avalia **conjuntos prontos para rodar**.

Uma **composição** é a união de um motorista com um ou mais veículos — o pacote que efetivamente sai para a estrada. O sistema verifica se **todos** os documentos de **ambos** estão válidos e conferidos.

- Se estiver tudo certo, a composição é liberada.
- Se faltar um documento ou algum estiver vencido, a composição é **bloqueada**, com a pendência apontada com clareza.

Esse é um dos argumentos mais fortes do produto: **não é um repositório de arquivos, é um semáforo operacional.**

Um detalhe que costuma surpreender em demonstração: **o usuário não cadastra motorista nem veículo.** Ele apenas envia os documentos — e as fichas do motorista e do veículo são criadas sozinhas, a partir do que foi lido. A única coisa que se cadastra manualmente é a composição, ligando um ao outro.

---

# 5. O que o sistema faz sozinho, todos os dias

Mesmo sem ninguém logado, a plataforma trabalha:

| Quando | O que acontece |
|---|---|
| Todo dia, à meia-noite | Verifica quais contratos venceram |
| Todo dia, de madrugada | Recalcula a validade de **todos** os documentos e marca os vencidos |
| Todo dia, de madrugada | Tenta reprocessar o que ficou pendente no dia anterior |
| Todo dia, de manhã | Dispara os avisos de vencimento |
| A cada hora | Gera os relatórios agendados |
| A cada hora | Verifica se os sites dos órgãos oficiais estão no ar |

Os **avisos de vencimento** são enviados com **90, 45, 30, 15 e 7 dias de antecedência**, com o PDF do documento anexado ao e-mail. O gestor não precisa lembrar de nada.

---

# 6. Como as pessoas são avisadas

O AutoChecker conversa por **quatro canais**, e cada pessoa escolhe como quer ser avisada, por tipo de assunto:

- **E-mail**
- **WhatsApp**
- **Notificação push** (no celular e no navegador)
- **Central de avisos dentro do próprio sistema**

Há ainda um recurso pouco explorado comercialmente: o cliente pode configurar **horários e dias em que aceita receber avisos**. Uma notificação que cairia às 3h da manhã fica guardada e sai no próximo horário permitido.

O motorista também pode interagir **pelo WhatsApp** — consultar pendências, receber alertas e enviar documentos direto pela conversa.

---

# 7. Cada empresa no seu ritmo

Dentro da plataforma, cada empresa configura:

- **Quem entra e o que cada um pode fazer** — são mais de 30 permissões diferentes, organizadas em grupos (quem só vê, quem envia, quem aprova, quem administra).
- **Quais módulos usa** — por exemplo, a conferência oficial de documentos é um módulo que pode ou não estar contratado.
- **Limites de uso** — quantidade de usuários, espaço de armazenamento, volume de envios.
- **Regras de senha** próprias.
- **Acesso para gente de fora** — motoristas e parceiros que não fazem parte da empresa podem receber um link de cadastro e, após aprovação, enviar seus documentos.

Tudo isso é registrado: **toda ação relevante fica gravada** — quem enviou, quem editou, quem excluiu, quem aprovou, com data e hora. Em auditoria ou fiscalização, a trilha existe.

---

# 8. E quando algo dá errado?

Nenhum sistema que depende de sites do governo e de fotos tiradas por celular funciona 100% do tempo. O AutoChecker foi construído contando com isso.

- **Se o site do órgão oficial estiver fora do ar**, o sistema percebe (ele checa a cada hora) e nem tenta consultar — evita travar a fila e marca o documento como "indisponível" para tentar depois.
- **Se um envio falhar**, o sistema tenta de novo automaticamente, com intervalos crescentes, antes de desistir.
- **Se um documento ficar parado**, a rotina da madrugada o recoloca na fila.
- **Se algo for excluído por engano**, existe exclusão reversível — o dado não some de imediato.

> 💡 **Como usar isso na comunicação:** resiliência vende melhor que perfeição. "O sistema sabe quando o órgão oficial está fora do ar e se reorganiza sozinho" é uma afirmação verdadeira e mais convincente do que prometer disponibilidade total.

---

# 9. Números que você pode usar com segurança

Todos verificados na documentação oficial do produto:

| Afirmação | Número |
|---|---|
| Tipos de documento suportados | **17** |
| Extratores especializados (um por tipo) | **14** |
| Fontes oficiais consultadas para conferência | **9** |
| Sites de órgãos monitorados continuamente | **6** |
| Canais de comunicação | **4** |
| Tipos de aviso automático | **19** |
| Marcos de aviso de vencimento | **90, 45, 30, 15 e 7 dias** |
| Arquivos por envio | até **10** |
| Tamanho por arquivo | até **20 MB** |
| Tipos de ação registrados em auditoria | **20** |
| Formatos de relatório | **PDF e Excel** |
| Frequências de relatório | **7** (de diária a anual) |

---

# 10. O que evitar dizer

Esta seção existe para proteger o time de uma promessa que o produto não sustenta.

> 🔴 **Não dizer "conferência em tempo real" sem ressalva.** A conferência depende de sites de órgãos públicos, que saem do ar com frequência. O certo é: *"conferência automática junto às fontes oficiais"*.

> 🔴 **Não dizer "leitura 100% precisa" ou "sem erros".** O sistema classifica a qualidade da própria leitura justamente porque ela varia conforme a foto enviada. O certo é: *"leitura automática com avaliação de qualidade"*.

> 🔴 **Não anunciar aplicativo móvel como disponível.** A documentação registra que o AutoChecker Mobile **ainda está em desenvolvimento**. Hoje o acesso é pelo navegador (que funciona bem no celular) e pelo WhatsApp.

> 🔴 **Não prometer "detecção de fraude".** O produto **confere autenticidade junto à fonte oficial** — que é diferente de analisar a imagem em busca de adulteração. Há verificação facial disponível, mas o argumento central é a consulta oficial.

> 🟠 **Cuidado ao falar de isolamento de dados na Base Compartilhada.** Ver a ressalva da seção 2.

---

# 11. O resumo para uma conversa de elevador

> O AutoChecker é um porteiro digital para a documentação de frota.
>
> A empresa manda os documentos — ou o próprio motorista manda, pelo WhatsApp. O sistema lê, entende o que é, confere com o governo, avisa com antecedência quando está vencendo e libera (ou trava) o motorista e o caminhão para rodar.
>
> Ninguém digita nada. Ninguém precisa lembrar de nada. E fica tudo registrado para a fiscalização.
