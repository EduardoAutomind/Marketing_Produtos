# Auditoria de Conformidade — Etapa 7 (AutoChecker) contra o texto oficial da LGPD

> **Cronograma de Observabilidade · AutoChecker · Onda 0 (Saneamento da Base)**
> `Objeto: cruzar os 2 documentos da Etapa 7 entre si e contra a Lei nº 13.709/2018 (Lgpd.md) · Confiança: Sei`

| | |
|---|---|
| **Produto** | AutoChecker |
| **Data da auditoria** | 19/06/2026 |
| **Documentos auditados** | `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` (doravante **DOC-CONSENT**) · `Etapa7_Scrubbing_PII_LGPD_Frontend_AutoChecker.md` (doravante **DOC-SCRUB**) |
| **Norma de referência** | `Lgpd.md` — Lei nº 13.709/2018, edição Senado Federal atualizada até jun/2024 |
| **Método** | (1) verificação factual cruzada entre os dois docs; (2) conferência artigo-a-artigo de cada citação legal contra o texto da lei; (3) busca por lacunas e imprecisões |

---

## Veredito geral

**Os dois documentos estão coerentes entre si e juridicamente corretos no essencial.** Não há contradição factual entre eles: descrevem os mesmos achados de código, os mesmos arquivos/linhas, o mesmo plano de remediação e o mesmo veredito (não cumprida, risco LGPD, gate da Onda 0).

A tese central — **"o Sentry coleta além do autorizado por configuração-padrão, e atualizar a política não cura a ilegalidade"** — **resiste à conferência contra o texto da LGPD.** Os artigos invocados existem e dizem o que os documentos afirmam.

Foram encontradas **3 imprecisões pontuais de citação** (todas de baixa gravidade, não derrubam o argumento) e **5 lacunas** — artigos da LGPD que **reforçariam** a conclusão e que ficaram de fora. Nenhum erro material foi encontrado.

| Dimensão auditada | Resultado |
|---|---|
| Consistência factual entre DOC-CONSENT e DOC-SCRUB | ✅ Conforme (sem divergências) |
| Citações da LGPD conferem com o texto oficial | 🟡 Conforme com 3 imprecisões menores |
| Solidez da tese jurídica | ✅ Sustentada pela letra da lei |
| Completude (artigos que faltaram) | 🟡 5 oportunidades de reforço |
| Plano de remediação coerente nos 2 docs | ✅ Idêntico e consistente |

---

## 1. Consistência factual entre os dois documentos

Cruzamento item a item dos fatos técnicos afirmados. **Tudo bate.**

| Fato técnico | DOC-SCRUB | DOC-CONSENT | Confere? |
|---|---|---|---|
| `sendDefaultPii: true` em 3 configs | `instrumentation-client.ts:21`, `sentry.server.config.ts:16`, `sentry.edge.config.ts:17` | mesmos 3 arquivos/linhas | ✅ |
| `Sentry.setUser({ id, email })` | `useAuth.tsx:175` (login) e `:388` (tenant) | mesmas 2 linhas | ✅ |
| Session Replay sem máscara | `0.1` / `1.0`, `instrumentation-client.ts:18-19`, sem `maskAllText`/`blockAllMedia` | idem | ✅ |
| Vazamento no serviço Custos | `AutoChecker_Custos/src/instrument.ts:12` | mesma linha | ✅ |
| Backend protegido por convenção | `send_default_pii` cai em `False` por padrão | idem (recomendação 5) | ✅ |
| Ambiguidade dos 2 frontends | `AutoChecker_Frontend/` vs `AutoChecker/frontend/` | mesma ressalva (recomendação 2) | ✅ |
| Plano de remediação | PII off + máscara + setUser só `id` + scrubbing server-side + corrigir Custos | tabela §6 idêntica | ✅ |
| Classificação | Onda 0 · GATE · Confiança "Sei" · Não cumprida | Onda 0 · gate · "Sei" | ✅ |

**Conclusão:** os documentos são **duas vistas do mesmo achado** — DOC-SCRUB é a entrega técnica; DOC-CONSENT é a leitura jurídica. Não se contradizem em nenhum ponto factual.

---

## 2. Conferência das citações LGPD contra o texto oficial

Cada dispositivo citado nos documentos foi localizado no `Lgpd.md` e comparado.

| Citação no documento | Texto real na LGPD (Lgpd.md) | Veredito |
|---|---|---|
| **Legítimo interesse = art. 7º, IX** | Art. 7º, IX: *"quando necessário para atender aos interesses legítimos do controlador ou de terceiro, exceto no caso de prevalecerem direitos e liberdades fundamentais do titular…"* | ✅ **Correto** |
| **Dado sensível = art. 5º, II** | Art. 5º, II: *"dado pessoal sensível: … dado referente à saúde ou à vida sexual, dado genético ou biométrico…"* | ✅ **Correto** — ASO (saúde) se enquadra |
| **Regime de dado sensível = art. 11** | Art. 11, I: consentimento *"de forma específica e destacada, para finalidades específicas"*; II: hipóteses restritas (a–g) | ✅ **Correto** |
| **Minimização = art. 6º, III (necessidade)** | Art. 6º, III: *"necessidade: limitação do tratamento ao mínimo necessário… não excessivos em relação às finalidades"* | ✅ **Correto** — é o pilar mais forte do argumento |
| **Consentimento livre/informado/específico = art. 8º** | Art. 8º trata da **forma** do consentimento; §4º: *"O consentimento deverá referir-se a finalidades determinadas, e as autorizações genéricas… serão nulas"* | 🟡 **Impreciso** — ver §3.1 |
| **Transferência internacional** (citada via Política 5) | Cap. V, arts. 33–36 governam a matéria na LGPD | 🟡 **Incompleto** — ver §3.2 |
| **Comunicação à ANPD em incidente** (via Política 7.2) | Art. 48: dever de comunicar à ANPD e ao titular incidente com *"risco ou dano relevante"* | ✅ **Correto** (mapeamento implícito) |

---

## 3. Imprecisões pontuais (baixa gravidade — corrigir para rigor)

### 3.1 "Consentimento livre, informado e específico (art. 8º)"
DOC-CONSENT §9, item 4, atribui ao **art. 8º** a exigência de consentimento *"livre, informado e específico"*.
**Ajuste:** a definição *"manifestação livre, informada e inequívoca"* está no **art. 5º, XII**. O **art. 8º** cuida da forma (por escrito/cláusula destacada, §1º) e da nulidade de autorizações genéricas (§4º). A exigência de **especificidade/destaque** para dado sensível vem do **art. 11, I**.
**Recomendação:** citar **art. 5º, XII + art. 8º, §4º + art. 11, I** em vez de "art. 8º" isolado. O raciocínio permanece válido; muda só a âncora legal.

### 3.2 Transferência internacional ancorada apenas na Política 5
Ambos os documentos tratam a transferência ao exterior como problema, mas a apoiam na **cláusula 5 da Política**, sem citar a base legal da própria LGPD.
**Ajuste:** a transferência internacional é regida pelo **Cap. V (arts. 33 a 36)**. O art. 33 lista **taxativamente** as hipóteses permitidas; enviar **dado de saúde** sem hipótese do art. 33 (combinado com a falta de base do art. 11) é o reforço legal que falta.
**Recomendação:** acrescentar **art. 33** ao lado da Política 5.

### 3.3 "Filmar e enviar a SaaS no exterior não se encaixa em nenhuma hipótese do art. 11"
A afirmação está **correta**, mas convém deixar explícito **por quê**: as hipóteses do art. 11 que poderiam ser invocadas (tutela da saúde — alínea *f*; proteção da vida — *e*) exigem finalidade de saúde/vida, e a finalidade do Sentry é **depuração técnica**. O documento conclui certo, mas sem percorrer as alíneas.
**Recomendação:** citar nominalmente art. 11, II, *e* e *f*, mostrando que a finalidade não corresponde.

> Nenhuma das três imprecisões altera a conclusão. São refinamentos de citação.

---

## 4. Lacunas — artigos da LGPD que reforçariam (e ficaram de fora)

Estes dispositivos **fortalecem** a tese e não foram usados:

| Artigo da LGPD | Como reforça a Etapa 7 |
|---|---|
| **Art. 6º, I (finalidade)** | *Purpose limitation*: o tratamento tem de ser para *"propósitos legítimos, específicos, explícitos e informados…, sem tratamento posterior incompatível"*. Capturar documento numa ferramenta cuja finalidade é **erro técnico** é desvio de finalidade — argumento independente da minimização. |
| **Art. 46, §2º (segurança desde a concepção)** | *"As medidas… deverão ser observadas desde a fase de concepção do produto até a sua execução."* Subir o SDK com `sendDefaultPii: true` (default invasivo) viola **privacy by design** — é exatamente o oposto. |
| **Art. 16 + Art. 18, IV** | Fundamentam a recomendação de **purgar replays já gravados**: dado tratado em desconformidade deve ser **eliminado** (art. 18, IV); a conservação só é lícita nas hipóteses do art. 16. Hoje a recomendação de purga aparece sem âncora legal. |
| **Art. 48 (incidente de segurança)** | Dá base ao gatilho de **comunicação à ANPD/titular**. A exposição pretérita de dado sensível em SaaS estrangeiro pode configurar incidente com *"risco relevante"* → avaliar dever de reporte. |
| **Art. 11, §4º e §5º** | Vedam o **uso compartilhado de dado de saúde para vantagem econômica**. **Nuance importante:** aqui o compartilhamento **não** é para vantagem econômica, então o documento **acertou** em apoiar-se no *caput* do art. 11 (falta de base legal), e **não** no §4º. Vale registrar a distinção para antecipar a objeção. |

---

## 5. Solidez da tese jurídica (a lógica fecha?)

A espinha dorsal do DOC-CONSENT é: **"reescrever a política não basta; é preciso parar de coletar (Etapa 7)."** Conferência:

1. **Necessidade/minimização (art. 6º, III)** — ✅ texto confirma. O excesso não vira lícito por aviso prévio. Argumento mais forte e bem ancorado.
2. **Dado sensível (art. 11)** — ✅ regime restrito confirmado; nenhuma redação de política cria base legal inexistente.
3. **Consentimento de terceiro (motorista/ASO)** — ✅ coerente com a moldura controlador/operador (**art. 5º, VI/VII** + **art. 39**): a AutoMind, como **operadora** desses documentos, não amplia finalidade unilateralmente. O documento usa essa moldura corretamente, embora cite os papéis pela via do Termo 6.2, não pelos artigos.
4. **Consentimento "empacotado" não é livre (art. 8º, §4º)** — ✅ autorizações genéricas são nulas; o raciocínio do *take-it-or-leave-it* é consistente.

**Conclusão:** a tese **"primeiro a Etapa 7 conserta a legalidade; depois a documentação dá transparência"** está **alinhada à letra da LGPD**. A ordem proposta (corrigir comportamento → revisar documentos) é juridicamente correta.

---

## 6. Riscos confirmados (mantêm-se após a auditoria)

| Risco | Severidade | Status |
|---|---|---|
| **ASO (saúde) em Session Replay → SaaS estrangeiro** sem base do art. 11 | 🔴 Máxima | Confirmado pelos 2 docs e pela lei |
| Corpo de request / replay com **CNH/CPF** (excesso, art. 6º III) | 🟠 Alta | Confirmado |
| **E-mail** anexado a todo evento (`setUser`) — fere minimização | 🟡 Média | Confirmado |
| **Custos** com `sendDefaultPii: true` (mesma exposição) | 🟠 Alta | Confirmado |
| **Exposição pretérita** (replays já retidos no Sentry) → possível incidente art. 48 | 🟠 Alta | A investigar com DPO |

---

## 7. Pontos a verificar (não são erros, são confirmações pendentes)

1. **E-mail do DPO** citado no DOC-CONSENT (`autochecker@automind.co`) usa TLD `.co`, enquanto o domínio corporativo conhecido é `automind.com.br`. **Confirmar** o endereço correto antes de acionar o DPO.
2. **Frontend canônico** — os 2 documentos repetem a ambiguidade `AutoChecker_Frontend/` vs `AutoChecker/frontend/`. Continua **em aberto**; precisa de confirmação do time (afeta itens 1, 2, 7 e 11).
3. **DPA com o Sentry** — a Política 4.1.a pressupõe acordo de tratamento compatível com a LGPD; verificar se existe e se cobre a transferência internacional (art. 33 / Política 5).

---

## 8. Recomendações da auditoria

**Para os documentos (rigor de citação — opcional, não bloqueia):**
1. Corrigir a âncora do consentimento: **art. 5º, XII + art. 8º, §4º + art. 11, I** (em vez de "art. 8º").
2. Adicionar **art. 33** à discussão de transferência internacional.
3. Acrescentar **art. 6º, I (finalidade)** e **art. 46, §2º (privacy by design)** como reforços independentes da minimização.
4. Ancorar a recomendação de purga em **art. 18, IV + art. 16**, e o gatilho de reporte em **art. 48**.

**Para a execução (inalteradas — a auditoria confirma):**
5. Tratar a Etapa 7 como **prioridade de compliance** (gate da Onda 0), não só observabilidade.
6. Aplicar a remediação técnica idêntica descrita nos 2 docs (PII off, máscara de replay, `setUser` só `id`, scrubbing server-side, corrigir Custos).
7. Acionar o DPO para avaliar **exposição pretérita** e eventual **reporte à ANPD**.

---

## 9. Conclusão

> **Está tudo em conformidade entre os dois documentos? — Sim.** Eles são factualmente consistentes e descrevem o mesmo achado sob duas óticas (técnica e jurídica), sem contradição.
>
> **As afirmações jurídicas conferem com a LGPD? — Sim, no essencial.** Todas as bases legais centrais (art. 6º III, art. 5º II, art. 11, art. 7º IX) estão corretas. Há **3 imprecisões menores de citação** e **5 oportunidades de reforço**, nenhuma das quais derruba a conclusão.
>
> **A inconformidade apontada é real?** — Sim. O cruzamento com o texto da lei **confirma**: o tratamento atual (PII automática + replay sem máscara + ASO/saúde → SaaS no exterior) **excede** a base legal de monitoramento que o cliente aceitou e **viola** os princípios da finalidade e da necessidade (art. 6º, I e III), com o agravante do regime de dado sensível (art. 11). A correção é a **Etapa 7**; a revisão documental é complementar e posterior.

---

### Referências cruzadas

| Item | Por quê |
|---|---|
| `Lgpd.md` | Norma de referência desta auditoria (Lei nº 13.709/2018) |
| **DOC-SCRUB** — Etapa 7 (entrega técnica) | Fonte dos achados de código |
| **DOC-CONSENT** — Termo/Política vs Sentry | Fonte da leitura jurídica |
| **Etapa 5** — consolidar init | Fixar `send_default_pii=False` explícito |
| **Etapa 11** — revisar `@sentry/nextjs` | Decidir frontend produtivo + PII no replay |
| **Item 31** (compliance) | Criptografia de CPF/CNPJ em repouso (fora do escopo de obs.) |
