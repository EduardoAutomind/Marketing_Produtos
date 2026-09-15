# Etapa 7 — Scrubbing de PII/LGPD no Frontend + Data Scrubber server-side

> **Cronograma de Observabilidade · AutoChecker**
> `Onda 0 (Saneamento da Base) · Camada: Frontend · Esforço: M (2–5 dias)`
> `Status no cronograma: Não iniciado · Veredito real: Não cumprida · Confiança: Sei`

| | |
|---|---|
| **Produto** | AutoChecker |
| **Onda** | 0 — Saneamento da Base (**GATE**: nada de ampliação antes de fechar) |
| **Fonte** | Detalhamento Ondas 0–4 (Item 7) — código real + documentação + Sentry ao vivo |

> ℹ️ **Vocabulário:** no cronograma, "**etapa**" = **item numerado** (coluna `# | Etapa`). As fases grandes são as "**Ondas**". Esta é a **Etapa/Item 7**, dentro da **Onda 0**.

---

## Em uma frase

É a etapa que **impede o Sentry de capturar e armazenar dados pessoais sensíveis** (CPF, CNPJ, e-mail, telas com CNH/ASO) dos usuários. Hoje o frontend está **vazando esses dados** para o Sentry — risco direto de **LGPD**.

---

## Por que ela existe (o problema real)

O backend já está protegido por convenção (`send_default_pii` cai em `False` por padrão). O **frontend, não**. O código mostra três buracos confirmados:

1. **`sendDefaultPii: true`** em **três** arquivos de configuração:
   - `instrumentation-client.ts:21`
   - `sentry.server.config.ts:16`
   - `sentry.edge.config.ts:17`
   - → manda dados pessoais (IP, headers, cookies, corpo de request) junto com cada evento.

2. **Identificação do usuário com e-mail:** `Sentry.setUser({ id, email })` em:
   - `modules/auth/hooks/useAuth.tsx:175` (login)
   - `modules/auth/hooks/useAuth.tsx:388` (troca de tenant)
   - → o e-mail vira PII anexada a todo erro.

3. **Session Replay sem máscara:** `replaysSessionSampleRate: 0.1` / `replaysOnErrorSampleRate: 1.0` (`instrumentation-client.ts:18-19`), mas **sem** `maskAllText` nem `blockAllMedia`.
   - → grava em vídeo as telas reais — incluindo **CNH, ASO, CPF** — usando só os defaults do SDK.

**Vazamento extra (fora do frontend):** o serviço **Custos** também está com `sendDefaultPii: true` (`AutoChecker_Custos/src/instrument.ts:12`).

> A documentação (§8) confirma tudo isso e aponta agravantes: `.env.example` expondo `NEXT_PUBLIC_JWT_SECRET` e CPF/CNPJ em texto puro no banco.

---

## O que precisa ser entregue (o "como resolver")

1. **Nos 3 configs do frontend:** trocar para `sendDefaultPii: false` **e** ligar a máscara do replay:
   - `maskAllText: true`
   - `blockAllMedia: true`
   - seletores específicos nas telas de documentos (CNH / ASO / CPF).
2. **`Sentry.setUser`:** enviar só `id` (sem `email`), ou anonimizar.
3. **Advanced Data Scrubbing (server-side, no painel do Sentry):** criar regras para CPF/CNPJ/e-mail como **rede de segurança** — pega o que escapar do código.
4. **Corrigir o Custos** (`sendDefaultPii: false`).

---

## Pontos de atenção (ressalvas reais)

- **Qual frontend está em produção?** Existem **dois** frontends com config Sentry quase idêntica (`AutoChecker_Frontend/` e `AutoChecker/frontend/`). Antes de aplicar, **confirmar com o time qual faz deploy** — e, se ambos forem deployados, corrigir os dois. (Essa ambiguidade afeta também os itens 1, 2 e 11.)
- A proteção do backend é por **convenção do SDK**, não há linha explícita. É correto, mas frágil — vale **fixar `send_default_pii=False` explicitamente** ao consolidar o init (cruza com a **Etapa 5**).
- Criptografar CPF/CNPJ em repouso é **compliance puro**, fora do escopo de observabilidade (cruza com o item 31) — fica como nota, não como entrega desta etapa.

---

## Por que é importante (e por que está na Onda 0)

A Onda 0 é um **gate**: nada de ampliar observabilidade antes de sanear a base. Esta etapa não é "nice-to-have" técnico — é **exposição de dados sensíveis de usuários reais**, com risco jurídico (LGPD).

**Âncoras legais (LGPD nº 13.709/2018):** o conteúdo capturado fere a **necessidade/minimização** (art. 6º, III) e a **finalidade** (art. 6º, I — desvio de propósito); o ASO é **dado de saúde sensível** sem base legal do **art. 11** (as alíneas *e*/*f* exigem finalidade de saúde/vida, não depuração técnica); subir o SDK com `sendDefaultPii: true` contraria a **segurança desde a concepção** (art. 46, §2º — *privacy by design*); a transferência ao SaaS estrangeiro depende das hipóteses **taxativas** do **art. 33**; e os replays já gravados em desconformidade devem ser **eliminados** (art. 18, IV, c/c art. 16), com eventual **comunicação de incidente** (art. 48). Detalhamento jurídico completo no anexo `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` e na auditoria `Etapa7_Auditoria_Conformidade_LGPD_Consentimento_vs_Scrubbing_AutoChecker.md`.

Não envolve métrica de Sentry para medir progresso; é **configuração de SDK + regras no painel**. Logo, o "pronto" é verificável lendo os 3 configs e checando as regras de scrubbing.

---

## Referências cruzadas

| Item relacionado | Por quê |
|---|---|
| **Análise de Consentimento** — `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` | Leitura jurídica deste achado: Termo/Política × o que o Sentry captura |
| **Auditoria de Conformidade** — `Etapa7_Auditoria_Conformidade_LGPD_Consentimento_vs_Scrubbing_AutoChecker.md` | Conferência artigo-a-artigo dos 2 docs contra o texto da LGPD |
| **Etapa 5** — Consolidar init no `init_sentry` | Fixar `send_default_pii=False` explicitamente ao consolidar |
| **Etapa 11** — Revisar `@sentry/nextjs` | Mesma decisão "qual frontend é o produtivo" + redução de PII no replay |
| **Itens 1 e 2** | Também dependem de confirmar o frontend canônico |
| **Item 31** (compliance) | Criptografia de CPF/CNPJ em repouso (fora do escopo de obs.) |
