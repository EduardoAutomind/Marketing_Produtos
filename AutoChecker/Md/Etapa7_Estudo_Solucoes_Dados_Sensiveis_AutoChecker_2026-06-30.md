# Etapa 7 — Estudo de Soluções para o Tratamento de Dados Sensíveis na Telemetria

> **Cronograma de Observabilidade · AutoChecker · Onda 0 (Saneamento da Base — GATE)**
> `Objeto: reunir o que se sabe da Etapa 7 e levantar ALTERNATIVAS de solução para o problema de manipular dado sensível no Sentry`
> `Gerado: 2026-06-30 · Confiança geral: Sei (com flags por item) · Citações revalidadas contra o código hoje`

| | |
|---|---|
| **Produto** | AutoChecker (driver) — reflexos em AutoLoad V4 e AutoMed |
| **Pergunta** | Como sanar, na prática, o tratamento de dados pessoais e **sensíveis** (CPF/CNH/ASO) que hoje pode chegar ao Sentry? Quais são os **caminhos alternativos**? |
| **Fontes** | (1) Código real em `Produtos/Autochecker/**` (`arquivo:linha`, lido hoje) · (2) Documentos da Etapa 7 (consentimento, scrubbing, auditoria, playbook) · (3) Documentação oficial do Sentry (Replay Privacy, Server-Side Scrubbing) via MCP |

---

## Em uma frase

A Etapa 7 existe para **impedir que dado pessoal e sensível chegue ao Sentry sem base legal**. Este estudo reúne o diagnóstico (já corrigido contra o código de hoje) e abre **seis camadas de defesa** com soluções alternativas — separando o que **você executa sozinho**, o que **depende do dev** e o que é **jurídico/arquitetural** — para você escolher a combinação certa.

---

## ⚠️ Correção material em relação aos documentos anteriores da Etapa 7

Ao revalidar o código hoje (30/06), um ponto dos documentos anteriores **mudou de figura** e precisa ser registrado — a precisão importa mais que manter a narrativa antiga.

| O que os docs anteriores diziam | O que o código de hoje mostra | Veredito |
|---|---|---|
| "Session Replay **sem máscara** → grava em vídeo as telas reais com CNH/ASO/CPF" | O replay é iniciado como `Sentry.replayIntegration()` **sem argumentos**, e o SDK é **`@sentry/nextjs ^10.43.0`** (`package.json:41`). Na doc oficial do SDK v8+, os **defaults** de `replayIntegration()` já são **`maskAllText: true`**, **`maskAllInputs: true`** e **`blockAllMedia: true`**. | 🟡 **Superestimado.** Por padrão, o texto **já é mascarado** (`*`) e a mídia (`img/svg/video/object/picture/embed/audio`) **já é bloqueada** antes de sair do browser. O "filme de ASO" **não** é o cenário default. |
| Risco máximo = "ASO em vídeo no replay → SaaS estrangeiro" | O vetor real e **inequívoco** é o **`sendDefaultPii: true`** (request bodies, headers, cookies, IP) + **e-mail no `setUser`**. É por aí que dado sensível em trânsito chega ao Sentry. | 🔴 **Reancorar o risco** no `sendDefaultPii`, não no replay. |

> **Por que isso não desarma a Etapa 7 — apenas a reaponta:** o dado sensível (CPF/CNH/ASO) **continua podendo chegar ao Sentry**, mas pelo **corpo de requisição/resposta e contexto de erro** que o `sendDefaultPii: true` anexa (especialmente no runtime server/edge do Next.js, que processa documentos), **não** pelo vídeo do replay. A inconformidade LGPD (necessidade art. 6º III, finalidade art. 6º I, dado sensível art. 11, transferência art. 33) **permanece** — muda o **mecanismo**, e portanto muda a **prioridade das soluções**.

**Ressalvas que mantêm o replay sob observação (Flag: Parcial — reverificar, não assumir resolvido):**
- `blockAllMedia` cobre `img/svg/video/object/picture/embed/audio`, **mas não `<canvas>`**. Se alguma tela renderiza documento via canvas (ex.: pdf.js, visualizador de imagem), confirmar que o canvas não é gravado.
- Máscara é **best-effort**; a própria doc do Sentry pede testar antes de produção. Conferir que **não há** seletores `unmask`/`sentry-unmask` liberando telas de documento.
- Confirmar que a versão que **builda em produção** é mesmo a v10 (não um lockfile antigo).

---

## 1. Diagnóstico consolidado (o que se sabe, verificado hoje)

Os achados de código, **revalidados linha a linha em 30/06**:

| # | Achado | Local (revalidado hoje) | Confirma? |
|---|---|---|---|
| 1 | `sendDefaultPii: true` (client) | `AutoChecker_Frontend/instrumentation-client.ts:21` **e** `AutoChecker/frontend/instrumentation-client.ts:21` | ✅ |
| 2 | `sendDefaultPii: true` (server) | `.../sentry.server.config.ts:16` (nos **dois** frontends) | ✅ |
| 3 | `sendDefaultPii: true` (edge) | `.../sentry.edge.config.ts:17` (nos **dois** frontends) | ✅ |
| 4 | `Sentry.setUser({ id, email })` | `AutoChecker_Frontend/.../useAuth.tsx:175` e `:388`; `AutoChecker/frontend/.../useAuth.tsx:196` e `:478` | ✅ (linhas mudaram no 2º front) |
| 5 | `sendDefaultPii: true` (serviço Custos) | `AutoChecker_Custos/src/instrument.ts:12` | ✅ |
| 6 | Replay com **defaults de máscara** (v10) | `instrumentation-client.ts:12` → `replayIntegration()` + `package.json:41` (`^10.43.0`) | ✅ (corrige doc anterior) |
| 7 | **Dois frontends** quase idênticos | `AutoChecker_Frontend/` vs `AutoChecker/frontend/` | ✅ — **ainda em aberto qual é o de produção** |
| 8 | Backend protegido por **convenção** (sem linha explícita) | `send_default_pii` cai em `False` por padrão | ✅ (frágil; cruza Etapa 5) |

**Os quatro vetores de risco, reordenados pela severidade real:**

1. 🔴 **`sendDefaultPii: true` (5 pontos)** — anexa IP, cookies, headers e **corpos de request/response** aos eventos. É o canal por onde CPF/CNH/**ASO** em trânsito pode ir ao Sentry. **Causa-raiz nº 1.**
2. 🟠 **E-mail no `setUser`** — PII identificável em todo evento. Fere minimização.
3. 🟡 **Session Replay** — *largamente mitigado pelos defaults do SDK v10*; risco **residual** (canvas/unmask/versão de build). Reverificar, mas não é a manchete.
4. 🔴 **Transferência internacional + dado sensível** — qualquer dado que vaze (via vetor 1) vai para SaaS no exterior. Aciona **art. 33** (transferência) e **art. 11** (se houver dado de saúde). **Persiste enquanto o vetor 1 existir.**

**Âncoras legais (já auditadas artigo-a-artigo contra a Lei nº 13.709/2018):** necessidade/minimização **art. 6º III**; finalidade **art. 6º I**; dado sensível **art. 5º II + art. 11**; consentimento **art. 5º XII + art. 8º §4º + art. 11 I**; *privacy by design* **art. 46 §2º**; transferência internacional **art. 33**; eliminação do tratado em desconformidade **art. 16 + art. 18 IV**; incidente **art. 48**.

---

## 2. O princípio organizador: defesa em profundidade

Em vez de uma única correção, dado sensível em telemetria se resolve melhor com **camadas** — se uma falha, a outra segura. Cada solução abaixo é mapeada a uma camada e a **quem executa**.

```
 [DADO]
   │   Camada 5 — APLICAÇÃO: o dado nunca vira telemetria (logar só ID/hash)
   ▼
 [SDK no browser/servidor]
   │   Camada 1 — ORIGEM: sendDefaultPii:false, setUser id, beforeSend, máscara
   ▼
 [Saída da rede AutoMind]
   │   Camada 2 — TRÂNSITO: Sentry Relay escrubando antes de sair da infra
   ▼
 [Ingestão Sentry]
   │   Camada 3 — DESTINO: Advanced Data Scrubbing server-side (painel)
   ▼
 [Armazenamento Sentry SaaS]
   │   Camada 4 — RESIDÊNCIA: self-hosted/BR → mata a transferência internacional
   ▼
 [Governança] Camada 6 — JURÍDICO: DPA/SCC, RIPD, retenção, purga, transparência
```

---

## 3. Menu de soluções alternativas (por camada)

Para cada solução: **o que resolve**, **esforço**, **quem executa** (🧍 você sozinho / 👨‍💻 dev / ⚖️ DPO-jurídico) e **flag de confiança**.

### Camada 1 — Na origem (SDK) · 👨‍💻 dev

| Cód. | Solução | O que resolve | Esforço | Flag |
|---|---|---|---|---|
| **A1** | `sendDefaultPii: false` nos **5 pontos** (client/server/edge dos 2 fronts + Custos) | **Corta o vetor nº 1** — IP, cookies, headers, **bodies** deixam de ser anexados | P | **Sei** |
| **A2** | `Sentry.setUser({ id })` — sem `email` | Remove PII identificável de todo evento | P | **Sei** |
| **A3** | Hook **`beforeSend` / `beforeSendTransaction`** removendo campos `cpf/cnh/aso/laudo/...` do payload **antes de sair do browser/servidor** | Rede de segurança **na origem** — vale mesmo se alguém reativar PII | P–M | **Sei** |
| **A4** | Replay: **manter os defaults** (já mascara) + adicionar `mask`/`block` nas telas de documento + classes `sentry-block` no container do ASO/CNH | Blinda o residual do replay (canvas/elementos específicos) | P | **Sei** |
| **A5** | Backend: fixar `send_default_pii=False` **explícito** ao consolidar o init (cruza **Etapa 5**) | Tira a proteção do "por convenção" (frágil) | P | **Sei** |
| **A6** | Custos: `sendDefaultPii: false` (`instrument.ts:12`) | Mesma exposição, mesmo remédio | P | **Sei** |

> **A1 é a correção de maior impacto e menor esforço de todo o estudo.** Se só uma coisa for feita pelo dev, é essa.

### Camada 2 — No trânsito · 👨‍💻 dev + 🧍 infra/config

| Cód. | Solução | O que resolve | Esforço | Flag |
|---|---|---|---|---|
| **B1** | **Sentry Relay** (proxy *open-source* do próprio Sentry) na rede da AutoMind, com `pii_config`/datascrubbing centralizado; SDKs apontam o DSN/tunnel para o Relay | **Política única de scrubbing** que vale para os 8 projetos, **independe de cada SDK**, e escruba **antes de o dado sair da infra**. Reduz a dependência de um PR por produto | M–G | **Parcial** (validar esforço de operar o Relay e o ponto de deploy) |

> Vantagem estratégica do Relay para o seu contexto: a regra de PII passa a ser **infra/configuração** (mais perto do que você controla) em vez de espalhada no código de cada produto. Custo: é um componente a **operar e manter**.

### Camada 3 — No destino (painel Sentry) · 🧍 você sozinho, sem PR

| Cód. | Solução | O que resolve | Esforço | Flag |
|---|---|---|---|---|
| **C1** | **Advanced Data Scrubbing server-side** (CPF/CNPJ/e-mail/`extra.**`/`$message`) — *já há playbook pronto* | Rede de segurança na **ingestão**; pega o que escapar do código | P–M | **Sei** |
| **C2** | "Prevent Storing of IP Addresses" + regra `$user.geo.**` | Remove IP e geolocalização derivada | P | **Sei** |
| **C3** | **Purga** de eventos/issues/replays já gravados em desconformidade | Trata a exposição **pretérita** (art. 16 + 18 IV) | M | **Parcial** (sem purga em massa trivial; alinhar DPO) |
| **C4** | Reduzir **data retention** da org/projeto (minimização temporal) | Menos tempo de exposição do que entrar | P | **Parcial** (depende do plano Sentry) |

> A camada 3 é **100% executável por você hoje**, sem dependência de dev. É a forma de **avançar a Etapa 7 sozinho** enquanto a camada 1 espera o PR. **Não substitui** a camada 1 (não corrige a causa-raiz).

### Camada 4 — Residência de dados (arquitetura) · 👨‍💻 dev/infra + ⚖️

| Cód. | Solução | O que resolve | Esforço | Flag |
|---|---|---|---|---|
| **D1** | **Sentry self-hosted** (em nuvem própria/BR) | Dado **não sai do país** → **elimina a transferência internacional** (art. 33) e a dependência do DPA-exterior | G | **Parcial** (custo/operação a avaliar com infra) |
| **D2** | Sentry SaaS com **região EU/US** (não há região BR) | Não resolve o art. 33 (ainda é exterior), mas EU dá salvaguardas mais fáceis (cláusulas-padrão) | M | **Sei (não resolve plenamente)** |
| **D3** | Ferramenta **compatível com SDK Sentry** auto-hospedada (ex.: GlitchTip) | Mesma instrumentação, dado em BR — alternativa de menor custo que o Sentry self-hosted | G | **Parcial** (validar paridade de features) |

> A camada 4 é a única que ataca a **transferência internacional na raiz**. É decisão estrutural — só vale o estudo de viabilidade se o jurídico considerar o art. 33 um bloqueio real (dado sensível eleva esse peso).

### Camada 5 — Na aplicação (cultura/processo) · 👨‍💻 dev + 🧍 processo

| Cód. | Solução | O que resolve | Esforço | Flag |
|---|---|---|---|---|
| **E1** | **Política de logging**: nunca pôr CPF/CNH/ASO em mensagem de erro, tag ou contexto — logar só **ID interno / hash** | Faz o dado sensível **nunca virar telemetria** (a defesa mais forte) | M | **Sei** |
| **E2** | **Denylist de URLs** sensíveis para captura de body / não opt-in de bodies de endpoints de documento | Evita o body de endpoints de ASO/documento | P–M | **Sei** |
| **E3** | **Lint/pre-commit** barrando `sendDefaultPii: true` e padrões de PII em log | Impede o problema de **voltar** num PR futuro | M | **Sei** |

### Camada 6 — Governança jurídica · ⚖️ DPO + 🧍 você (redige/aciona)

| Cód. | Solução | O que resolve | Esforço | Flag |
|---|---|---|---|---|
| **F1** | **DPA + Cláusulas-Padrão (SCC)** com o Sentry (art. 33, II, *b*) | Dá base à transferência internacional **do que for legítimo** | M | **Parcial** (verificar se já existe) |
| **F2** | **RIPD/DPIA** do tratamento de telemetria | Documenta necessidade/proporcionalidade; exigível p/ dado sensível | M | **Sei** |
| **F3** | **Política de retenção** + purga pretérita + avaliar **art. 48** (incidente) | Encerra a exposição passada e define o futuro | M | **Parcial** (DPO decide reporte) |
| **F4** | Atualizar **Termo/Política** — **depois** de minimizar | Transparência do tratamento **mínimo** | P | **Sei** |

> **Ordem inegociável (já auditada):** F4 vem **por último**. Documento ajusta a *transparência*; a minimização (camadas 1–3) ajusta a *legalidade*. Reescrever a política **não** torna lícito coletar dado excessivo/sensível.

---

## 4. Matriz comparativa — qual solução ataca qual problema

| Solução | Corta causa-raiz (vetor 1)? | Protege dado sensível/ASO? | Resolve transferência internac. (art. 33)? | Quem | Esforço |
|---|:--:|:--:|:--:|:--:|:--:|
| **A1** PII off ×5 | ✅ | ✅ (no que vaza por body) | — | 👨‍💻 | P |
| **A2** setUser id | parcial | — | — | 👨‍💻 | P |
| **A3** beforeSend | ✅ (reforço) | ✅ | — | 👨‍💻 | P–M |
| **A4** replay mask+ | — | ✅ (residual) | — | 👨‍💻 | P |
| **B1** Relay | ✅ (centralizado) | ✅ | parcial (escruba antes de sair) | 👨‍💻+🧍 | M–G |
| **C1–C4** painel | ❌ (rede de segurança) | ✅ (no destino) | — | 🧍 | P–M |
| **D1/D3** self-host BR | — | ✅ | ✅ **(única que resolve)** | 👨‍💻 | G |
| **E1–E3** app/processo | ✅ (preventivo) | ✅ | — | 👨‍💻+🧍 | M |
| **F1** DPA/SCC | — | — | ✅ (legaliza) | ⚖️ | M |
| **F2–F4** governança | — | — | — | ⚖️+🧍 | M |

**Leitura da matriz:** nenhuma solução isolada fecha tudo. A causa-raiz é **A1**; o dado sensível pede **A1+A3+E1**; a transferência internacional só morre com **D1/D3** *ou* se legaliza com **F1**; e **C1–C4** é o que **você entrega hoje** sem ninguém.

---

## 5. Recomendação — a combinação ótima, em 3 fases

### P0 · Hoje, você sozinho (sem PR) 🧍
1. **C1–C4** no painel (já há playbook): Advanced Data Scrubbing org-wide + IP/geo off + retention.
2. **C3** purga do pretérito **com o DPO**.
3. Abrir os **3 tickets** (você executa C; dev recebe A; DPO recebe F).
4. **Resolver a ambiguidade do frontend canônico** (achado #7) — destrava A1/A2/A4.
> Comunicar honestamente: *"camada server-side aplicada; correção de origem ainda pendente no código."*

### P1 · Dev, baixo esforço / alto impacto 👨‍💻
5. **A1** (`sendDefaultPii:false` ×5) — **a correção nº 1**.
6. **A2** (setUser só id) + **A6** (Custos) + **A5** (backend explícito).
7. **A3** (`beforeSend` escrubando CPF/CNH/ASO) + **A4** (reforço de máscara no replay).
8. **E2/E3** (denylist de URL + lint) para não regredir.

### P2 · Estrutural / governança 👨‍💻⚖️
9. Decidir **B1 (Relay)** e/ou **D1/D3 (residência BR)** conforme o peso que o jurídico der ao art. 33.
10. **E1** (política de logging) como cultura.
11. **F1** (DPA/SCC), **F2** (RIPD), e só então **F4** (atualizar Termo/Política).

---

## 6. Anti-padrões (o que parece solução e não é)

| "Solução" | Por que falha |
|---|---|
| Só **reescrever o Termo/Política** | Não cura excesso (art. 6º III) nem cria base p/ dado sensível (art. 11). Auditado. |
| Só **Additional Sensitive Fields** por substring | Casa por pedaço de valor → **over-scrub** (some `"Unexpected"` se puser `exp`) ou *under-scrub*. É rede de segurança, não correção. |
| **Desligar o Replay** achando que resolve | O replay já está mascarado por default; desligá-lo **não toca** o vetor real (`sendDefaultPii`). Gasta a bala no alvo errado. |
| **Confiar só no scrubbing do painel** | Age na ingestão (destino), não na origem; o dado ainda **trafega** ao exterior antes de ser redigido. |
| Assumir "**está mascarado, então ok**" sem reverificar canvas/unmask/versão de build | Máscara é best-effort; precisa de teste real (a própria Sentry avisa). |

---

## 7. Flags de confiança (resumo)

| Afirmação | Flag |
|---|---|
| `sendDefaultPii:true` em 5 pontos é o vetor real e dominante | **Sei** (revalidado hoje) |
| Replay v10 mascara texto e bloqueia mídia por default | **Sei** (doc oficial + `package.json:41`) |
| Replay ainda tem residual (canvas/unmask/build) | **Parcial** — reverificar |
| A1 corta o vetor 1 com esforço P | **Sei** |
| Relay escruba antes de sair da infra | **Sei (conceito)** / **Parcial** (esforço de operar) |
| Self-host BR elimina a transferência internacional | **Parcial** (viabilidade/custo) |
| Não há região Sentry SaaS no Brasil | **Sei** |
| GlitchTip é compatível com SDK Sentry | **Parcial** (validar paridade) |
| Qual frontend é o de produção | **Não sei** — confirmar com o time |
| Existe DPA/SCC firmado com o Sentry | **Não sei** — confirmar |

---

## 8. Fontes

1. Código — `AutoChecker_Frontend/instrumentation-client.ts:12,18,19,21` e `AutoChecker/frontend/instrumentation-client.ts` (idêntico) — lido 30/06/2026.
2. Código — `.../sentry.server.config.ts:16`, `.../sentry.edge.config.ts:17` (ambos os fronts); `.../modules/auth/hooks/useAuth.tsx:175,388` e `:196,478`; `AutoChecker_Custos/src/instrument.ts:12`.
3. Código — `AutoChecker_Frontend/package.json:41` e `AutoChecker/frontend/package.json:41` → `@sentry/nextjs ^10.43.0`.
4. Sentry Docs (MCP) — **Session Replay › Privacy** (`/platforms/javascript/guides/nextjs/session-replay/privacy.md`): defaults `maskAllText:true`, `maskAllInputs:true`, `blockAllMedia:true`; `beforeAddRecordingEvent`; bodies de rede são opt-in.
5. Sentry Docs — **Server-Side Data Scrubbing** e **Advanced Data Scrubbing** (base do playbook C1–C4).
6. `Etapa7_Scrubbing_PII_LGPD_Frontend_AutoChecker.md` · `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` · `Etapa7_Auditoria_Conformidade_LGPD_Consentimento_vs_Scrubbing_AutoChecker.md` · `Etapa7_Playbook_DataScrubbing_Painel_Sentry_8Projetos_2026-06-30.md`.
7. `Lgpd.md` — Lei nº 13.709/2018 (edição Senado, jun/2024) — âncoras legais.
8. Memórias do projeto — `autochecker-etapa7-analise-lgpd`, `sentry-token-readonly`, `autochecker-trabalho-autonomo-vs-dev`.

---

### Referências cruzadas

| Item | Por quê |
|---|---|
| **Playbook de Data Scrubbing (painel)** | Detalha a execução da Camada 3 (C1–C4) passo a passo |
| **Análise de Consentimento / Auditoria LGPD** | Fundamento jurídico das âncoras citadas |
| **Etapa 5** — consolidar `init_sentry` | Onde fixar `send_default_pii=False` explícito (A5) |
| **Etapa 11** — revisar `@sentry/nextjs` | Decidir frontend canônico (achado #7) + PII no replay |
| **IntegrationLog (LGPD)** | Mesmo padrão de PII-em-telemetria num log de app próprio |
| **Item 31** (compliance) | Criptografia de CPF/CNPJ em repouso (fora do escopo de obs.) |
</content>
</invoke>
