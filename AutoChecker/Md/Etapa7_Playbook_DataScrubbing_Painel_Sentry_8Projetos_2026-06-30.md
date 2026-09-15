# Etapa 7 — Playbook de Data Scrubbing no painel do Sentry (sem deploy)

> **Cronograma de Observabilidade · AutoChecker (driver) + todos os 8 projetos**
> `Onda 0 (Saneamento da Base) · Camada: Configuração de painel · Esforço: P–M`
> `Gerado: 2026-06-30 · Executável por: você (sem dependência de dev/PR)`

| | |
|---|---|
| **Driver** | Etapa 7 do AutoChecker — captura de PII/dado de saúde (ASO) acima do autorizado |
| **Escopo** | Os 8 projetos Sentry da org `automind-qd` |
| **Natureza** | **100% painel** (Settings → Security & Privacy). Não toca código, não precisa de merge. |
| **Fontes** | Doc oficial Sentry: *Server-Side Data Scrubbing*, *Advanced Data Scrubbing*, *Event PII Fields* (links na §10) |

---

## Em uma frase

O Sentry permite **redigir dados sensíveis no servidor, no momento da ingestão, antes de gravar** — configurado inteiramente pelo painel. Isso te deixa **reduzir o risco LGPD da Etapa 7 agora**, como rede de segurança, **enquanto a correção no código (SDK) espera o dev**.

---

## A fronteira honesta: o que o painel resolve e o que NÃO resolve

Isto é o ponto mais importante do documento — para você não comunicar "resolvido" além do que é verdade.

| Risco da Etapa 7 | Painel resolve? | Flag |
|---|---|---|
| CPF / CNPJ / RG / e-mail em mensagens de erro, tags, `extra`, request | **Sim** — regras server-side redigem na ingestão | **Sei** |
| IP do usuário sendo armazenado | **Sim** — toggle "Prevent Storing of IP Addresses" | **Sei** |
| Geolocalização derivada do IP | **Sim** — regra avançada `$user.geo.**` | **Sei** |
| Texto dentro de **Session Replay** (campos digitados, labels) | **Parcial** — replay honra regras server-side de texto, mas o confiável é mascarar no SDK (`maskAllText`) | **Parcial** |
| **Vídeo/imagem de documentos** no replay (CNH, ASO escaneado) | **Não** — bloquear mídia (`blockAllMedia`) é client-side, exige código | **Sei (que não resolve)** |
| Causa-raiz `sendDefaultPii: true` | **Não** — é flag do SDK, exige código | **Sei (que não resolve)** |
| Dados **já capturados** no passado (replays/eventos pretéritos) | **Parcial** — dá para purgar manualmente (§7), mas não é automático | **Parcial** |

**Conclusão:** este playbook entrega o **item 3** da Etapa 7 (a rede de segurança server-side) e mitiga risco real **hoje**. Ele **não substitui** os itens 1, 2 e 4 (correção do SDK), que continuam com o dev. Comunicar como *"camada de proteção server-side aplicada; correção de origem ainda pendente no código"*.

---

## Como o scrubbing server-side funciona (3 mecanismos)

Tudo fica em **Settings → Security & Privacy**, e existe em **dois níveis**: **organização** (vale para os 8 projetos) e **projeto** (um a um).

> ⚠️ **Precedência:** se houver configuração de *Data Scrubbing* na **organização, ela sobrepõe** a do projeto — para usar o nível de projeto nesses toggles, desligue o da org primeiro. Já as **regras de Advanced Data Scrubbing** podem coexistir, e **regra avançada tem precedência até sobre os Safe Fields**.

**1) Data Scrubber padrão (já vem ligado — confirmar).**
Redige automaticamente:
- valores que parecem **cartão de crédito**;
- valores cujo **conteúdo ou nome da chave** contenha: `password`, `secret`, `passwd`, `api_key`, `apikey`, `auth`, `credentials`, `mysql_pwd`, `privatekey`, `private_key`, `token`, `bearer`.

**2) Additional Sensitive Fields (lista de chaves/valores).**
Você adiciona nomes de campo. O Sentry remove qualquer campo com aquele nome **e** qualquer *valor* que **contenha** aquela string.
> ⚠️ **Cuidado com over-scrubbing:** como casa por substring no valor, um termo curto/comum apaga demais (ex.: pôr `exp` faz sumir `"Unexpected error"`). Use nomes **específicos** (`cpf`, `cnh`), nunca pedaços genéricos.

**3) Advanced Data Scrubbing (regras finas).**
Cada regra = **Método** × **Tipo de dado** × **Origem (selector)**:
- **Métodos:** `Remove` (apaga o campo), `Mask` (troca por `*`), `Hash` (troca por hash), `Replace` (troca por `[Filtered]`).
- **Tipos de dado:** Credit Card, **Email Addresses**, IP Addresses, **Regex Matches** (dialeto **Rust**; `(?i)` p/ ignorar caixa), `Anything`, US SSN (não serve p/ Brasil), etc.
- **Origem (onde olhar):** `$string` (qualquer string), `$message` (mensagem de log), `$error.value` (texto da exceção), `$user.geo.**`, `extra.**`, `$http.headers.x-token`, `tags.nome`, `$frame.vars.x`…

**Safe Fields** = exceções, para *não* redigir algo (ex.: preservar `user.id` para contagem de usuários). Use caminho completo (`user.id`) para não liberar `extra.id` junto.

---

## Os 8 projetos e a prioridade

| Projeto Sentry | Produto | Prioridade | Por quê |
|---|---|---|---|
| `autochecker-frontend` | AutoChecker | 🔴 **Alta** | Replay + telas com CNH/ASO/CPF (driver da Etapa 7) |
| `autochecker-backend` | AutoChecker | 🔴 **Alta** | Processa documento/ASO (dado de saúde) |
| `autochecker-worker` | AutoChecker | 🔴 **Alta** | Jobs sobre os mesmos dados |
| `autoloadv4-frontend` | AutoLoad V4 | 🟠 Média | PII de usuário (já tem prod) |
| `autoloadv4-portal-cliente` | AutoLoad V4 | 🟠 Média | PII de cliente |
| `autoloadv4-backend` | AutoLoad V4 | 🟡 Baixa | PII de negócio; ainda sem DSN de prod |
| `autoloadv4-edgegateway` | AutoLoad V4 | 🟡 Baixa | Headers/tokens (default já cobre auth) |
| `automed` | AutoMed | 🟠 Média | Domínio médico → potencial dado de saúde |

> A regra base (CPF/CNPJ/e-mail/IP) faz sentido **org-wide** (cobre os 8 de uma vez). As regras de **dado de saúde/ASO** e de **replay** são específicas do AutoChecker (e talvez AutoMed) → nível de projeto.

---

## Parte A — Base, no nível da organização (cobre os 8)

`Settings (org) → Security & Privacy → seção DATA SCRUBBING`

- [ ] **Data Scrubber** = **ON** (confirmar que está ligado).
- [ ] **Use Default Scrubbers** = ON.
- [ ] **Prevent Storing of IP Addresses** = **ON**.
  - ℹ️ A geolocalização ainda é derivada do IP mesmo com isto ligado → trate na Parte B (regra `$user.geo.**`).
- [ ] **Additional Sensitive Fields** — adicione (um por linha), termos **específicos** do contexto BR:
  ```
  cpf
  cnpj
  rg
  cnh
  aso
  exame
  laudo
  prontuario
  paciente
  motorista
  nome_completo
  data_nascimento
  telefone
  celular
  endereco
  ```
  > `password`, `token`, `auth`, `secret`, `api_key`, `bearer` já são cobertos pelo default — não precisa repetir.
- [ ] **Safe Fields** — adicione `user.id` (preserva contagem de usuários sem expor o resto do objeto `user`).

---

## Parte B — Regras avançadas (Advanced Data Scrubbing)

`Settings → Security & Privacy → Advanced Data Scrubbing → Add Rule`

Aplique no **nível da organização** as 1–4 (genéricas) e no **projeto AutoChecker** (e AutoMed) as 5–6.

| # | Método | Tipo de dado | Origem (Source) | Cobre |
|---|---|---|---|---|
| 1 | **Mask** | Regex `(?i)\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b` | `$string` | **CPF** (com ou sem pontuação) |
| 2 | **Mask** | Regex `\b\d{2}\.?\d{3}\.?\d{3}/?\d{4}-?\d{2}\b` | `$string` | **CNPJ** |
| 3 | **Mask** | Email Addresses | `$string` | **E-mails** em qualquer campo |
| 4 | **Remove** | Anything | `$user.geo.**` | **Geolocalização** derivada do IP |
| 5 | **Remove** | Anything | `$message` **e** `$error.value` | Conteúdo de **documento colado em mensagem de erro** |
| 6 | **Remove** | Anything | `extra.**` | Anexos de contexto ("Additional Data") que carreguem ASO/dados do exame |

Notas de execução:
- O dialeto de regex é **Rust** — teste em regex101.com selecionando *Rust*. Não use `/.../g`; escreva só o padrão.
- O campo opcional **"event ID"** acima de *Source* serve para **autocompletar** os caminhos a partir de um evento real — útil para achar o nome exato de uma chave em `extra`. O event ID não é salvo.
- Regras avançadas valem **só para eventos novos** (going forward).
- ⚠️ **CNH (11 dígitos)**: evitei uma regra genérica de 11 dígitos porque colide com IDs/protocolos → **falso-positivo**. Se quiser cobrir CNH, faça via *Additional Sensitive Fields* pelo nome da chave (`cnh`), já incluído na Parte A. **Flag: Parcial.**

---

## Parte C — Session Replay (AutoChecker)

- **No painel:** as regras de texto acima também se aplicam ao texto dos replays (honram o scrubbing server-side). **Flag: Parcial** — reduz, não garante.
- **O que o painel NÃO faz:** bloquear o **vídeo das telas** com imagem de CNH/ASO. Isso é `maskAllText: true` + `blockAllMedia: true` no SDK = **código, com o dev** (já documentado em `Etapa7_Scrubbing_PII_LGPD_Frontend_AutoChecker.md`).
- **Ação sua:** registrar no ticket que, até o `blockAllMedia` entrar, vale **reduzir/zerar `replaysOnErrorSampleRate`** temporariamente — mas isso também é config de SDK (dev). No painel, dá para você **desativar a feature Replay do projeto** se a área jurídica exigir parada imediata. **Flag: Parcial.**

---

## Parte D — Logs estruturados (quando existirem)

- Logs **honram as regras de Data Scrubbing padrão** do projeto automaticamente.
- Para regras avançadas em logs, ao criar a regra **escolha o dataset de Logs**. Selectors `**`, `$string` e `$number` valem para todos os datasets; para um atributo específico, selecione o atributo do log.
- **Flag: Sei (conceito) / Parcial (uso)** — vocês ainda não emitem logs estruturados; deixar a regra pronta para quando a feature for ligada.

---

## Parte E — Purgar o que já foi capturado (passado)

Scrubbing só vale daqui pra frente. Para o que já está gravado:

- **Eventos/issues:** abrir a issue → ícone de **lixeira** (deleta a issue inteira; não dá para deletar um evento isolado).
- **Tags:** `Project Settings → Tags` → remover o valor da tag que carregou PII (deletar a issue não limpa a tag).
- **Replays já gravados em desconformidade:** alvo de eliminação (LGPD art. 16 c/c art. 18, IV). **Flag: Parcial** — confirmar com o DPO o procedimento; não há "purga em massa" trivial no painel.
- **Caso extremo** (PII espalhada em muitas issues): deletar e recriar o projeto. **Não fazer sem alinhar com o dev** (perde histórico e muda DSN).

---

## Parte F — Validar

1. Após salvar, gerar/aguardar um evento novo no projeto.
2. Abrir o evento → link **"JSON"** (mostra o payload cru que o scrubber enxerga) → confirmar que o campo aparece como `[Filtered]`, `null` ou mascarado.
3. Conferir um replay novo do AutoChecker para o texto.
4. Marcar no checklist quais projetos já passaram.

---

## O que isto vira no board (sua entrega)

- **Ticket 1 (você executa e fecha):** "Aplicar Data Scrubbing server-side (Partes A–B) na org + 3 projetos AutoChecker" — sem dev.
- **Ticket 2 (depende do dev — você redige completo):** "Etapa 7 SDK: `sendDefaultPii=false`, `maskAllText`, `blockAllMedia`, `setUser` só id" — referência ao doc de frontend.
- **Ticket 3 (DPO):** "Eliminar replays/eventos pretéritos em desconformidade + DPA com Sentry."

Assim você **avança a Etapa 7 sozinho** (Partes A–F) e deixa o resto **destravado e sem ambiguidade** para quem tem a permissão de código.

---

## Flags de confiança (resumo)

| Afirmação | Flag |
|---|---|
| Scrubbing server-side é configurável só no painel e age na ingestão | **Sei** |
| Regras (CPF/CNPJ/e-mail/IP/geo) redigem em eventos novos dos 8 projetos | **Sei** |
| Org override sobre projeto nos toggles de Data Scrubbing | **Sei** |
| Texto do Session Replay é reduzido pelas regras server-side | **Parcial** |
| Vídeo de documentos no replay precisa de `blockAllMedia` (código) | **Sei (que não resolve no painel)** |
| Regra de CNH por regex sem falso-positivo | **Não sei** (por isso uso a chave `cnh`) |
| Purga em massa de replays pretéritos pelo painel | **Não sei** (validar com DPO) |

---

## Fontes (10)

1. Sentry Docs — **Server-Side Data Scrubbing** — https://docs.sentry.io/security-legal-pii/scrubbing/server-side-scrubbing/
2. Sentry Docs — **Advanced Data Scrubbing** (métodos, tipos, selectors, dialeto Rust) — https://docs.sentry.io/security-legal-pii/scrubbing/advanced-datascrubbing/
3. Sentry Docs — **Event PII Fields** (campos redigidos por padrão) — https://docs.sentry.io/security-legal-pii/scrubbing/server-side-scrubbing/event-pii-fields/
4. Sentry Docs — **Advanced Data Scrubbing → Data Scrubbing for Logs**
5. Org/projetos confirmados via Sentry MCP (`automind-qd`: 8 projetos) — 2026-06-30
6. `Etapa7_Scrubbing_PII_LGPD_Frontend_AutoChecker.md` (parte SDK/código)
7. `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` (âncoras LGPD)
8. `Etapa7_Auditoria_Conformidade_LGPD_Consentimento_vs_Scrubbing_AutoChecker.md`
9. Memória do projeto — `sentry-token-readonly` (MCP só lê; curadoria vai pelo painel)
10. Memória do projeto — `autochecker-etapa7-analise-lgpd`
