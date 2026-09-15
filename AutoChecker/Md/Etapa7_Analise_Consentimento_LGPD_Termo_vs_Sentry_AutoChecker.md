# Análise de Consentimento — O Termo de Uso e a Política de Privacidade autorizam o que o Sentry captura?

> **Cronograma de Observabilidade · AutoChecker · Anexo da Etapa 7 (Scrubbing PII/LGPD)**
> `Onda 0 (Saneamento da Base) · Foco: Compliance LGPD x Telemetria Sentry · Confiança: Sei`

| | |
|---|---|
| **Produto** | AutoChecker |
| **Pergunta de negócio** | O cliente deu permissão para usarmos esses dados, ou é o Sentry que está buscando essa informação por conta própria? |
| **Fontes analisadas** | `Termo de Uso _ AutoChecker.html` (v2.0, 27/04/2026) · `Política de Privacidade _ AutoChecker.html` (v1.0, 27/04/2026) · `Etapa7_Scrubbing_PII_LGPD_Frontend_AutoChecker.md` · doc oficial do SDK `@sentry/nextjs` (opção `sendDefaultPii`) |
| **Data da análise** | 18/06/2026 |

---

## Conclusão direta (TL;DR)

**Parcialmente — e justamente na parte que mais importa, NÃO.**

Os documentos jurídicos autorizam a AutoMind a enviar **dados técnicos/telemetria** para ferramentas de monitoramento (o Sentry se enquadra como **suboperador**). **Porém eles NÃO autorizam o que o `sendDefaultPii: true` + Session Replay sem máscara estão realmente fazendo:** capturar conteúdo de documentos pessoais e **sensíveis** (CNH, CPF e, sobretudo, ASO = dado de saúde) e transmitir isso a um SaaS de terceiros hospedado fora do Brasil.

> **A hipótese do time está correta:** é o **Sentry "puxando" esse dado automaticamente** (por configuração-padrão do SDK), e esse comportamento **extrapola a base legal** que o cliente aceitou. O documento que o cliente assinou diz uma coisa; o código faz outra, mais invasiva.

---

## 1. O que os documentos EFETIVAMENTE autorizam ✅

Ao aceitar o Termo (cláusula **2.1**), o usuário aceita também a Política, incorporada por referência (cláusula **2.3**). Esse aceite cobre:

| Base legal | Onde está | O que autoriza |
|---|---|---|
| **Legítimo interesse** (art. 7º, IX, LGPD) | Termo **6.4** | tratamento de "**telemetria, métricas de uso e dados vinculados à segurança da informação e ao monitoramento operacional da plataforma**" |
| **Legítimo interesse** | Política **3.1.b** | "monitoramento de desempenho, disponibilidade e integridade operacional"; "prevenção a fraudes, acessos não autorizados e uso indevido" |
| **Suboperadores / prestadores** | Política **4.1.a** | "ferramentas de **monitoramento, analytics e suporte técnico**, limitadas às finalidades operacionais" → **é aqui que o Sentry se enquadra** |
| **Dados de acesso e uso** | Política **2.3** | IP e dados de rede; user-agent; data/hora/fuso com NTP; páginas visitadas, ações e funcionalidades; identificadores de sessão e tokens |
| **Transferência internacional** | Política **5** | dados podem ser armazenados/processados fora do Brasil, mediante cláusulas contratuais padrão |
| **Logs de auditoria** | Termo **7.1** | NTP, identificação do usuário, IP, user-agent, hash; retenção de 24 meses |

➡️ **Enviar dados de erro/performance/telemetria ao Sentry (stack trace, rota, latência, status HTTP, evento de erro) está AUTORIZADO** — cabe no legítimo interesse de monitoramento e na figura do suboperador de monitoramento.

---

## 2. O que o Sentry está REALMENTE fazendo (o gap)

A Etapa 7 identificou três falhas no frontend. Cruzando cada uma com o que a flag `sendDefaultPii: true` coleta (confirmado na documentação oficial do SDK):

### 2.1 `sendDefaultPii: true` (3 arquivos)
- `instrumentation-client.ts:21`
- `sentry.server.config.ts:16`
- `sentry.edge.config.ts:17`

Equivale a **ligar todas as categorias de coleta automática de PII**:

| Categoria | Dado enviado ao Sentry |
|---|---|
| `userInfo` | `user.id`, `user.email`, `user.username`, **IP** |
| `httpHeaders` | headers de request e response |
| `httpBodies` | **corpo das requisições/respostas** (pode conter CPF/CNPJ/CNH em trânsito) |
| `cookies` | cookies |
| `queryParams` | parâmetros de URL |

> A denylist embutida do SDK escapa apenas valores cujas **chaves** batem com `auth`/`token`/`password`/similares — **não** cobre CPF/CNH/nome dentro do payload.

### 2.2 Session Replay sem máscara
`replaysSessionSampleRate: 0.1` / `replaysOnErrorSampleRate: 1.0` (`instrumentation-client.ts:18-19`), **sem** `maskAllText` nem `blockAllMedia`.
→ grava **em vídeo a tela real** do usuário — incluindo **CNH, ASO e CPF**.

### 2.3 Identificação com e-mail
`Sentry.setUser({ id, email })` em `modules/auth/hooks/useAuth.tsx:175` (login) e `:388` (troca de tenant).
→ o **e-mail** (PII) vai anexado a **todo** evento de erro.

### 2.4 Vazamento extra (fora do frontend)
Serviço **Custos** também com `sendDefaultPii: true` (`AutoChecker_Custos/src/instrument.ts:12`).

> **Ponto-chave:** nada disso é telemetria. É **o dado operacional/documental** — exatamente a categoria que a Política trata na cláusula **2.4** (CNH, CRLV, certidões, comprovantes), cujo tratamento é restrito "**sob instrução e responsabilidade do Assinante Controlador**".

---

## 3. O que NÃO está autorizado ❌ (cláusula por cláusula)

| Comportamento do Sentry | Cláusula em conflito | Por quê |
|---|---|---|
| Replay capturando CNH/CPF/ASO; body com documentos | **Termo 6.2** | Dado documental tem base legal "execução de contrato" e **só "nos limites da operação contratada"**. A operação é *validar/autenticar documento* — não *filmar a tela e enviar a um SaaS de erro*. |
| Mesmo replay / mesmo body | **Termo 6.4** | O legítimo interesse autônomo da AutoMind é **restrito** a "telemetria/métricas/segurança/monitoramento". Conteúdo de documento **não é** telemetria → fora dessa autorização. |
| `sendDefaultPii: true` em geral | **Termo 6.7** e **Política 6.1** | Viola o **princípio da minimização** expressamente prometido. `sendDefaultPii` é o oposto de minimizar. |
| Expor PII a terceiro fora do escopo | **Termo 4.3** | "É **vedado** […] expor dados pessoais ou segredos de negócio **fora do escopo da operação**." |
| Uso p/ melhoria/segurança sem anonimizar | **Termo 4.3** e **Política 3.1.b** | O uso para melhoria/segurança só é autorizado com dados "**agregados e anonimizados, sem possibilidade de reidentificação**". Um evento de Sentry com e-mail + IP + vídeo da sessão é **plenamente identificável**. |
| Transferência de dado sensível ao exterior | **Política 5** + **art. 33, LGPD** | A transferência internacional só é permitida nas hipóteses **taxativas** do art. 33; enviar **dado de saúde** sem hipótese do art. 33 (somado à falta de base do art. 11) é ilícito. A Política 5 pressupõe salvaguardas e finalidade legítima — não cobre dado sensível sem base. |

---

## 4. O ponto mais grave: dado pessoal SENSÍVEL (saúde) 🚨

O **ASO (Atestado de Saúde Ocupacional)** é **dado de saúde** = **dado pessoal sensível** (art. 5º, II + art. 11 da LGPD). Dado sensível tem regime **muito mais estrito**: exige consentimento **específico e destacado** ou hipótese legal própria do art. 11.

**Nenhum dos dois documentos** obtém consentimento específico para tratar dado de saúde — e muito menos para **transmiti-lo a um operador de monitoramento no exterior**. O Session Replay sem máscara faz exatamente isso, de forma automática e silenciosa.

> Este é o risco jurídico de **maior severidade** do conjunto: combina (a) dado sensível, (b) ausência de base legal específica, (c) transferência internacional e (d) retenção do material no Sentry (replays já gravados ficam armazenados).

> **Nota de precisão de citação:** a vedação reforçada do **art. 11, §§ 4º e 5º** (compartilhar dado de saúde **para obter vantagem econômica**) **não** é o fundamento aqui — o envio ao Sentry não visa vantagem econômica. O que falta é base legal no **caput do art. 11** (nenhuma das hipóteses dos incisos I e II se aplica). Registrar a distinção evita a objeção de que o §4º permitiria o tratamento.

---

## 5. Resposta objetiva à pergunta de negócio

> **"O cliente dá permissão de usarmos esses dados, ou na verdade é o Sentry que está buscando esse tipo de informação?"**

**As duas coisas — e o conflito é exatamente esse:**

1. O cliente **deu permissão para telemetria/monitoramento** (legítimo interesse + suboperador) → o Sentry *pode* existir no produto.
2. Mas o **Sentry coleta muito além disso por configuração-padrão** (`sendDefaultPii: true` + replay sem máscara + e-mail). Esse "a mais" — conteúdo de documentos, dados sensíveis, PII identificável — **não foi autorizado por nenhuma cláusula** e ainda **contraria** a promessa de minimização (6.7) e a vedação de exposição fora do escopo (4.3).

**Não há cobertura jurídica para o que está sendo capturado hoje.** O comportamento atual coloca a AutoMind em descumprimento da sua própria Política de Privacidade.

---

## 6. Como a Etapa 7 fecha o gap (alinhamento direto)

A remediação já desenhada na Etapa 7 é precisamente o que torna o código conforme ao que os documentos prometem:

| Entrega da Etapa 7 | Cláusula que passa a ser cumprida |
|---|---|
| `sendDefaultPii: false` nos 3 configs do frontend | Minimização (Termo 6.7 / Política 6.1); vedação de exposição (Termo 4.3) |
| `maskAllText: true` + `blockAllMedia: true` no replay (+ seletores nas telas de CNH/ASO/CPF) | Elimina captura de dado sensível → resolve o risco do art. 11 |
| `Sentry.setUser` só com `id` (sem e-mail) | Reduz PII identificável; aproxima do "anonimizado" exigido em 3.1.b |
| Advanced Data Scrubbing server-side (CPF/CNPJ/e-mail) no painel do Sentry | Rede de segurança para a minimização |
| Corrigir o serviço **Custos** (`sendDefaultPii: false`) | Mesma exposição, mesmo remédio |

➡️ Após a Etapa 7, o Sentry passa a receber **apenas telemetria** — exatamente o que o cliente autorizou. **O gap deixa de existir.**

---

## 7. Recomendações

1. **Tratar a Etapa 7 como prioridade de compliance, não só de observabilidade.** Está na Onda 0 (gate) e o achado de **dado de saúde (ASO) em SaaS estrangeiro** eleva a severidade para risco jurídico/ANPD, não apenas técnico.
2. **Confirmar qual frontend está em produção** (`AutoChecker/frontend` vs `AutoChecker_Frontend`, configs quase idênticos) antes de aplicar; se ambos deployam, **corrigir os dois**.
3. **Envolver o DPO** (`autochecker@automind.co`):
   - avaliar se houve **exposição pretérita** — replays já gravados com dados sensíveis permanecem retidos no Sentry e, se for o caso, devem ser **eliminados** (dado tratado em desconformidade → **art. 18, IV**; a conservação só é lícita nas hipóteses do **art. 16**, que aqui não se aplicam);
   - avaliar necessidade de registro/relato conforme a Política 7.2 e o **art. 48** (comunicação à ANPD **e ao titular** de incidente de segurança com risco ou dano relevante).
4. **Verificar o DPA com o Sentry.** A Política (4.1.a) pressupõe "acordos de tratamento de dados compatíveis com a LGPD" com suboperadores — confirmar que existe DPA firmado com o Sentry e que ele cobre a transferência internacional (Política 5 + **art. 33**, em especial a hipótese de cláusulas-padrão contratuais do **art. 33, II, *b***).
5. **Fixar `send_default_pii=False` explicitamente no backend** ao consolidar o init (cruza com a Etapa 5) — hoje a proteção é por convenção do SDK, sem linha explícita.

---

## 8. Mapa rápido: dado × autorização

| Dado enviado ao Sentry | Autorizado? | Base / Conflito |
|---|---|---|
| Stack trace, rota, status HTTP, latência | ✅ Sim | Telemetria/monitoramento (Termo 6.4 · Política 3.1.b · 4.1.a) |
| IP, user-agent, identificador de sessão | ✅ Sim (como telemetria/log) | Política 2.3 · Termo 7.1 |
| E-mail do usuário (`setUser`) | ⚠️ Não claramente | Fere minimização (6.7); deve ser anonimizado/só `id` |
| Corpo de request com CPF/CNPJ/CNH | ❌ Não | Fora do escopo da operação (6.2/6.4); vedação 4.3 |
| Session Replay com CNH/CPF na tela | ❌ Não | Idem acima + ausência de anonimização |
| Session Replay com **ASO (saúde)** | ❌ **Não — risco máximo** | Dado sensível, art. 11 LGPD; sem consentimento específico |

---

## 9. E se atualizarmos o Termo e a Política — dá para manter como está?

**Não. Atualizar os documentos NÃO substitui a Etapa 7 — a inconformidade permaneceria.**

É um equívoco comum supor que "se está escrito na política, está liberado". Consentimento e transparência são **necessários, mas não suficientes**: a LGPD tem **princípios substantivos** (art. 6º) que um contrato ou política **não pode afastar**.

### Por que só reescrever os documentos não resolve

1. **Princípios da finalidade e da necessidade/minimização (art. 6º, I e III) — o ponto mais forte.**
   Pela **necessidade** (art. 6º, III), só se pode tratar o dado **estritamente necessário** à finalidade. A finalidade do Sentry é **depurar erro técnico** — para isso ele precisa de stack trace, rota e status HTTP, **não** da CNH/CPF/ASO na tela. E, pela **finalidade** (art. 6º, I), o tratamento só vale para o propósito específico informado, **sem tratamento posterior incompatível**: capturar conteúdo de documento numa ferramenta cuja finalidade é erro técnico é **desvio de finalidade** — vício independente da minimização. O conteúdo capturado é **excessivo por definição**, e o excesso **não vira lícito** só por estar avisado na política.

2. **Dado sensível — ASO (saúde, art. 11): barreira praticamente intransponível.**
   Dado de saúde só pode ser tratado nas hipóteses **restritas** do art. 11. As duas únicas que poderiam ser invocadas exigem finalidade de saúde/vida — **proteção da vida ou da incolumidade física** (art. 11, II, *e*) e **tutela da saúde, por profissionais ou serviços de saúde** (art. 11, II, *f*) — e a finalidade do Sentry é **depuração técnica**, não saúde. "Filmar a tela e enviar a um SaaS de monitoramento no exterior" **não se encaixa em nenhuma** das alíneas (e ainda falta a necessidade). Nenhuma redação de política cria essa base legal.

3. **O titular, na maioria dos casos, nem aceita os nossos termos.**
   CNH e ASO são do **motorista/terceiro**, não do Assinante que clicou "aceito". Para esses documentos, o **Assinante é Controlador e a AutoMind é apenas Operadora** (Termo 6.2). A AutoMind **não pode ampliar unilateralmente** a finalidade, e atualizar **o nosso** Termo **não captura consentimento de quem não está no fluxo**. Não se consente por terceiro.

4. **Consentimento "empacotado" não é válido.**
   O consentimento é, por definição, manifestação **livre, informada e inequívoca** (art. 5º, XII); autorizações **genéricas são nulas** (art. 8º, §4º); e, por se tratar de dado sensível, ele teria de ser **específico e destacado** (art. 11, I). Embutir "aceito que minhas telas com documentos de saúde sejam gravadas e enviadas a terceiro estrangeiro" dentro de um aceite obrigatório (sem o qual a pessoa não usa o sistema) é *take-it-or-leave-it* — o que viola o "livre" (art. 5º, XII) e a especificidade (art. 8º, §4º + art. 11, I).

5. **Segurança e privacy by design (art. 46, §2º).**
   As medidas de proteção de dados devem ser observadas **desde a fase de concepção** do produto até a sua execução. Subir o SDK com `sendDefaultPii: true` (default invasivo) é o **oposto** de *privacy by design* — reforça que a inconformidade está na **engenharia**, não na redação do documento, e por isso a documentação não a sana.

### O que atualizar os documentos REALMENTE resolve

Atualizar a documentação tem valor — mas só na camada que **já é legítima**:

| Dado | Atualizar docs resolve? |
|---|---|
| Telemetria (erro, rota, performance) | ✅ Já coberto; documentar reforça transparência |
| IP / user-agent / sessão | ✅ Cobertura adequada |
| E-mail no `setUser` | 🟡 Sustentável com base legal + minimização — mas o ideal técnico é nem enviar |
| Conteúdo de documento (CNH/CPF) via body/replay | ❌ Continua excessivo (necessidade) |
| **ASO / dado de saúde** | ❌ **Continua ilícito** mesmo com consentimento na política |

### Conclusão da seção — a ordem correta

**Não dá para "manter assim e só ajustar os documentos".** A inconformidade não está na *falta de aviso* — está no **próprio ato de coletar dado excessivo e sensível sem necessidade**, e isso o contrato não cura.

A sequência correta é a inversa:

1. **Primeiro a Etapa 7 corrige o comportamento** (desligar PII, mascarar replay, scrubbing) → o sistema passa a coletar só o necessário e **sai da inconformidade**.
2. **Depois** a documentação pode ser revisada para refletir e dar transparência a esse tratamento mínimo.

> **Documento ajusta a *transparência*; a Etapa 7 ajusta a *legalidade*.** São complementares, mas é a Etapa 7 que de fato tira a AutoMind da inconformidade.

---

### Referências cruzadas

| Item relacionado | Por quê |
|---|---|
| **Etapa 7** — Scrubbing PII/LGPD | Entrega técnica que sana este gap |
| **Etapa 5** — Consolidar init no `init_sentry` | Fixar `send_default_pii=False` explicitamente |
| **Etapa 11** — Revisar `@sentry/nextjs` | Decisão "qual frontend é produtivo" + redução de PII no replay |
| **Item 31** (compliance) | Criptografia de CPF/CNPJ em repouso (fora do escopo de obs.) |
