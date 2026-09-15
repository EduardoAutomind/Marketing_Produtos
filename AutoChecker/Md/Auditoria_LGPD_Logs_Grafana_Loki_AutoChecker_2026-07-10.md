# Auditoria LGPD — PII em Logs (Grafana/Loki) — AutoChecker

| | |
|---|---|
| **Produto** | AutoChecker |
| **Data** | 2026-07-10 |
| **Alvo da auditoria** | Logs estruturados do backend em produção, ingeridos no Loki e visíveis no Grafana (`monitor.autochecker.cloud`) |
| **Pergunta de negócio** | O AutoChecker está registrando e-mail (e outros dados) de clientes nos logs do Grafana. Isso é problema de LGPD? Qual a base legal e o que fazer? |
| **Fontes** | (1) Loki ao vivo — datasource `loki` uid `ba808642…`, stream `job="autochecker-backend"`, `environment=prod`, `filename=/var/log/autochecker/api.log`; (2) Texto oficial da lei — `.claude/skills/lgpd-conformidade/reference/Lgpd.md` (Lei nº 13.709/2018) |
| **Método** | Skill `lgpd-conformidade` — toda afirmação legal citada artigo a artigo contra o texto oficial |

---

## 1. Conclusão direta (TL;DR) — **flag: Sei (fatos + artigos) / Parcial (retenção e acesso)**

**Sim, é um problema de LGPD** — mas o e-mail é a parte *menos* grave do que está sendo registrado. Há três achados de gravidade crescente:

1. 🔴 **Excesso de PII de identificação** — e-mail, nome, sobrenome e IP de clientes reais em **toda** requisição. Fere **minimização (art. 6º, III)**.
2. 🚨 **Vazamento de credencial de sessão** — o **token JWT `access`/`refresh` completo** é gravado no corpo de resposta do login. Isso **não é só LGPD, é falha de segurança** (art. 46): quem tiver leitura no Grafana replica a sessão e se passa pelo cliente.
3. 🟠 **Sem retenção definida** — dado pessoal em log sem prazo de eliminação previsto. Fere **arts. 15 e 16**.

Logar dado pessoal **não é ilícito em si** — observabilidade se ampara em **legítimo interesse (art. 7º, IX)**. O que reprova é o **excesso** e a **falha de segurança**, que a base legal não dispensa.

**Ordem de correção: comportamento primeiro, documento depois.** Reescrever a Política de Privacidade não cria base legal para o excesso nem tira o token do log.

---

## 2. Fatos do alvo (evidência ao vivo — Loki, janela 24h em 2026-07-10)

Cada requisição HTTP do backend gera uma linha JSON no stream `autochecker-backend`. Exemplo real (campos sensíveis destacados):

```json
{
  "method": "GET", "path": "/api/notifications/inbox/unread_count/",
  "status_code": 200, "duration_ms": 16.93,
  "tenant": {"id": "a9cdea0f-…", "schema": "base_compartilhada", "name": "Base Compartilhada"},
  "user_id": 61,
  "user_email": "flaviaminhuk@redepetro.com.br",   // ← e-mail de cliente real
  "ip": "177.200.79.2",                              // ← IP em toda linha
  ...
}
```

E no login, o corpo de resposta carrega a credencial:

```json
// POST /api/accounts/login/step2/  → response_body
{ "refresh": "eyJhbGciOiJIUzI1NiI…",   // ← token JWT completo
  "access":  "eyJhbGciOiJIUzI1NiI…",   // ← token JWT completo
  "user_info": "{…\"email\": \"paulo.sacramento@automind.co\"…}" }
```

### Dimensionamento (contagens `count_over_time` em 24h)

| Sinal | Ocorrências / 24h | Observação |
|---|---:|---|
| Linhas com `user_email` preenchido (não-null) | **5.966** | e-mail de cliente por linha |
| Linhas com `ip` preenchido | **6.232** | praticamente toda requisição |
| Linhas com token JWT (`eyJhbGci…`) no corpo | **89** | emissões de token em respostas de login |
| Eventos `/login/step1|step2` | **33** | fluxo de autenticação |

> Clientes externos reais identificados nas amostras: `@redepetro.com.br`, `@copercana.com.br`. Não são contas internas de teste.

### Já mascarado corretamente (crédito ao que existe)
- `"password": "***"` ✅
- `"has_cpf": "***"` ✅ (CPF não vaza)
- `"temp_token": "***"` ✅

O scrubbing **existe, mas é incompleto**: cobre senha/CPF/temp_token e **não cobre** e-mail, nome, IP e o token JWT final.

---

## 3. Classificação dos dados (art. 5º)

| Dado | Classificação | Âncora |
|---|---|---|
| E-mail | Dado pessoal | art. 5º, I — "informação relacionada a pessoa natural identificada ou identificável" |
| Nome / sobrenome | Dado pessoal | art. 5º, I |
| IP | Dado pessoal | art. 5º, I — identificável mesmo isolado (cruza com registro do provedor); vinculado ao `user_id` na maioria das linhas → identificado |
| Token JWT | Não é "dado" no sentido do art. 5º, mas **credencial de acesso** ao dado | art. 46 (segurança) |
| CPF | Dado pessoal | art. 5º, I — **já mascarado** ✅ |

**Não há dado pessoal sensível** (art. 5º, II — saúde, biometria, etc.) nestas linhas → o regime restrito do **art. 11 não incide** aqui. (Diferente da Etapa 7, onde havia ASO/saúde.)

**Papéis (art. 5º, VI/VII):** a AutoMind é **controladora** dos dados dos usuários do AutoChecker. O Grafana/Loki é ferramenta interna (self-hosted em `monitor.autochecker.cloud`) — tratamento pela própria controladora, não transferência a operador terceiro.

---

## 4. O que ESTÁ autorizado ✅

| Tratamento | Base legal |
|---|---|
| Registrar logs de requisição para operar/depurar o produto | **Legítimo interesse — art. 7º, IX** ("interesses legítimos do controlador") |
| Manter o **IP** para segurança (detecção de fraude/abuso/acesso indevido) | **Legítimo interesse — art. 7º, IX** — o IP é o campo onde essa base realmente se aplica |
| Identificar tecnicamente o usuário por `user_id` (pseudônimo) | art. 7º, IX + art. 6º, III (é o mínimo necessário) |

A observabilidade **em si** é lícita. O legítimo interesse do art. 7º, IX cobre a finalidade.

---

## 5. O que NÃO está ❌ (conflito artigo a artigo)

| Achado | Princípio/artigo violado | Por quê |
|---|---|---|
| **`user_email`, `first_name`, `last_name` em toda linha** | **Necessidade — art. 6º, III** ("limitação ao mínimo necessário […] não excessivos") | O `user_id` já identifica para depuração. E-mail e nome são excessivos — reprovam mesmo estando "avisados" em política |
| **Reuso do e-mail (coletado p/ autenticar) na observabilidade** | **Finalidade — art. 6º, I** | Dado coletado para operar o produto, replicado indefinidamente em ferramenta de monitoramento = finalidade diversa da informada |
| **Token JWT `access`/`refresh` no corpo de log** | **Segurança — art. 6º, VII + art. 46** | Credencial de sessão exposta a qualquer leitor do Grafana → risco de personificação do titular. Achado de **severidade máxima** |
| **Sem prazo de eliminação do log** | **Término/eliminação — arts. 15, I e 16** | Dado pessoal deve ser eliminado quando "deixou de ser necessário" (15, I) e "após o término do tratamento" (16). Log sem retenção = tratamento sem fim previsto |
| **Acesso ao Grafana/Loki** (a confirmar) | **Segurança — art. 46** | Se leitura do Loki não for restrita, amplia a exposição de todos os itens acima |

---

## 6. Tabela-resumo `Dado × Autorizado? × Base/Conflito`

| Dado tratado | Autorizado? | Base legal / Conflito (art. citado) |
|---|---|---|
| `user_id`, rota, status, duração, tenant | ✅ Sim | Legítimo interesse — art. 7º, IX + minimização OK (art. 6º, III) |
| `ip` | ⚠️ Sim, com parcimônia | Legítimo interesse/segurança — art. 7º, IX; mas preso à necessidade (art. 6º, III) e retenção (arts. 15/16) |
| `user_email` | ❌ Não (excessivo) | Fere minimização — art. 6º, III; desvio de finalidade — art. 6º, I |
| `first_name` / `last_name` | ❌ Não (excessivo) | Fere minimização — art. 6º, III |
| **Token JWT `access`/`refresh`** | ❌ Não — **risco máximo** | Fere segurança — art. 6º, VII + art. 46 |
| CPF (`has_cpf`) | ✅ Sim | Já mascarado `***` |
| Senha / temp_token | ✅ Sim | Já mascarado `***` |
| Retenção do log | ❌ Não definida | arts. 15, I e 16 |

---

## 7. Caminho de correção + ordem

**Princípio: parar de coletar o excessivo primeiro; documentar depois.**

| # | Ação | Artigo | Urgência |
|---|---|---|---|
| 1 | **Redigir o token JWT** (`access`/`refresh`) no `response_body` do login antes de logar (adicionar ao mesmo scrubber que já mascara senha/CPF) | art. 46 | 🚨 Imediata |
| 2 | **Remover `user_email`, `first_name`, `last_name`** do log estruturado; manter apenas `user_id`. Se o suporte precisar do e-mail, deixar em stream restrito ou hash | art. 6º, III / I | Alta |
| 3 | **Definir e aplicar retenção no Loki** (ex.: 30–90 dias) via `limits_config`/compactor | arts. 15/16 | Média |
| 4 | **Restringir acesso de leitura ao Grafana/Loki** a quem tem necessidade operacional | art. 46 | Média |
| 5 | Considerar **mascarar o último octeto do IP** (`177.200.79.x`) quando o IP cheio não for necessário | art. 6º, III | Baixa |
| 6 | **Só então documentar** o tratamento no registro de operações / política de logs (privacy by design demonstrável) | art. 6º, X + art. 46, §2º | Depois |

> O scrubber que hoje mascara `password`/`has_cpf`/`temp_token` já é o ponto de extensão natural para os itens 1 e 2 — é ampliar a lista de campos, não construir do zero.

---

## 8. Recomendações e pontos a verificar (Parcial)

- **[Parcial] Retenção atual do Loki** — não confirmada nesta auditoria. Verificar `limits_config.retention_period` / compactor. Se estiver sem retenção (`0s`), o log acumula indefinidamente.
- **[Parcial] Quem acessa o Grafana** — confirmar se a leitura do Loki é restrita ou aberta a toda a equipe. Define o tamanho real da exposição.
- **[Parcial] O mesmo padrão no stream `celery-tasks`** — auditar se as tasks também logam PII/token (não coberto aqui).
- **[Parcial] Frontend** — este estudo cobre o backend (`/var/log/autochecker/api.log`). Verificar se há log de frontend com PII.
- **[Sei] Onde corrigir** — a correção é de **configuração/código do produto** (o middleware/formatter de log do Django), não do Grafana. O Grafana só exibe o que recebe.

---

## 9. Referências cruzadas

- `Auditoria_LGPD_IntegrationLog_AutoChecker_2026-06-30.md` — mesmo padrão (telemetria capta PII sem retenção), no IntegrationLog.
- `Etapa7_Remediacao_Fechamento_Achados_PII_AutoChecker_2026-07-06.md` — fechamento do PII no Sentry (front+back); este achado é o **mesmo tema no pilar de logs/Loki**.
- `Etapa7_Scrubbing_PII_LGPD_Frontend_AutoChecker.md` — método de scrubbing de PII já aplicado no Sentry, reaproveitável aqui.
- `reference/Lgpd.md` — texto oficial (fonte da verdade): arts. 5º, 6º (I/III/VII/X), 7º (IX), 15, 16, 46.

---

*Gerado pela skill `lgpd-conformidade`. Toda base legal conferida contra o texto oficial da Lei nº 13.709/2018. Achados de fato validados ao vivo no Loki em 2026-07-10.*
