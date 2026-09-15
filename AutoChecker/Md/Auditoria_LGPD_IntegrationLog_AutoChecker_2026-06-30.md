# Auditoria LGPD — `IntegrationLog` do AutoChecker

**Produto:** AutoChecker
**Data:** 30/06/2026
**Fonte da lei:** `.claude/skills/lgpd-conformidade/reference/Lgpd.md` (Lei nº 13.709/2018, ed. Senado atualizada até jun/2024) — todo artigo citado abaixo foi conferido contra esse texto.
**Evidência de código (Azure DevOps, branch `dev`):**
- `shared/models/integrations.py` → classe `IntegrationLog`
- `backend/apps/integrations/serializers.py` → `IntegrationLogListSerializer`, `IntegrationLogDetailSerializer`
- `backend/apps/integrations/views.py` → `IntegrationLogViewSet` (filtros por entidade + ação `retry`) — PR 15213
- `shared/tasks/integration_tasks.py` → `_create_log`/`_update_log`
- Frontend `IntegrationTimeline*` (PR 15214) — expõe o log na UI

**Pergunta de negócio:** o `IntegrationLog` — que agora persiste o payload completo das integrações e o exibe na UI por motorista/veículo — está em conformidade com a LGPD? O que está autorizado, o que não está, e como corrigir?

---

## 1. Conclusão direta (TL;DR) — **Parcial → com não-conformidades**

**Manter um log de auditoria das chamadas de integração é legítimo** (legítimo interesse, art. 7º, IX + dever de registro do art. 37). **Porém**, a forma atual reprova em três pontos concretos:

1. 🔴 **Retenção indefinida** — `integrations_log` não tem TTL nem rotina de expurgo. PII fica armazenada para sempre. Fere **art. 15, I** e **art. 16** (eliminação após o fim do tratamento) e **art. 6º, III** (necessidade).
2. 🔴 **Excesso de coleta/armazenamento** — persiste `request_payload` e `response_body` **na íntegra** (CPF, CNH, nome, documentos), mais do que um log de auditoria/retry precisa. Fere **art. 6º, III** (minimização).
3. 🔴 **Possível vazamento de segredo** — o `curl_command`/`request_body` gravados podem conter o header `Authorization`/token do provider, e agora são exibidos na UI. Fere **art. 6º, VII** e **art. 46** (segurança) e **art. 46, §2º** (segurança desde a concepção).

Flag global: **Parcial** — a base legal do *registro* existe; o *desenho* (o quê se guarda, por quanto tempo, para quem se mostra) é que está em desconformidade. Há um ponto factual a confirmar (dado sensível e base_url no exterior) marcado abaixo.

---

## 2. Fatos — o que o `IntegrationLog` realmente trata

Campos persistidos (modelo `IntegrationLog`, `db_table="integrations_log"`, `app_label="tenants"` → **gravado no schema do tenant**, isolamento por tenant):

| Campo | Conteúdo | Natureza |
|---|---|---|
| `provider`, `event_type`, `status`, `response_status_code`, `retry_count`, `created_at`, `was_skipped`, `skip_reason` | metadados operacionais da chamada | técnico (não-pessoal) |
| `entity_id` | UUID do `DriverNode`/`VehicleNode` | identificador indireto de pessoa |
| `entity_type`, `approved` | tipo da entidade / flag de aprovação | técnico |
| **`request_payload`** (JSONField) | **payload completo enviado ao ERP** — `entity_data` do motorista/veículo: CPF, nome, CNH, documentos (MOPP, NR-20, NR-35, CRLV, CVV…) | **dado pessoal (PII)** |
| **`response_body`** (TextField) | **resposta completa do ERP externo** (pode devolver dados do titular) | **dado pessoal (potencial)** |
| `curl_command` / `request_body` (em `endpoint_payload`, via `_create_log`) | comando/body da requisição — **pode conter token/credencial no header** | **segredo** |
| `error_message` | mensagem de erro (pode ecoar payload) | variável |

**Acesso/UI:** o `IntegrationLogDetailSerializer` expõe `request_payload` **e** `response_body`; o `IntegrationTimelineModal` (PR 15214) mostra a timeline por entidade a qualquer usuário autenticado com `IntegrationsAccessPermission`. O `IntegrationLogViewSet` filtra por `provider__tenant=connection.tenant` → **sem vazamento cross-tenant** na consulta (isolamento OK).

**Quem é quem:** o cliente (transportadora/tenant) é **controlador** dos dados do motorista; a AutoMind/AutoChecker atua como **operador** (art. 5º, VII; art. 39). O destino da integração (ERP do cliente) é outro agente. Isso importa: o desenho do log (retenção, scrubbing) é decisão da AutoMind como operadora e impacta o cumprimento do art. 39 (seguir instruções do controlador) e art. 46/47 (segurança).

---

## 3. O que ESTÁ autorizado ✅

| Tratamento | Base legal (conferida) |
|---|---|
| **Registrar a chamada de integração** (event_type, status, status_code, timestamps, erro, retry) | **Legítimo interesse do controlador — art. 7º, IX** ("interesses legítimos… exceto no caso de prevalecerem direitos e liberdades fundamentais do titular"). Reforçado pelo **art. 37**: "O controlador e o operador devem manter registro das operações de tratamento… especialmente quando baseado no legítimo interesse." |
| **Reprocessar (retry) uma integração que falhou** | Execução da operação contratada / legítimo interesse — **art. 7º, V e IX**. Operação técnica de continuidade do serviço. |
| **Isolamento por tenant** na consulta | Boa prática de segurança — **art. 46** (medidas técnicas aptas a proteger contra acesso não autorizado). |

> Observação: legítimo interesse só cobre o **estritamente necessário** à finalidade (**art. 10, §1º**) — o que nos leva direto às não-conformidades abaixo.

---

## 4. O que NÃO está autorizado ❌

### 4.1 🔴 Retenção indefinida — art. 15, I + art. 16
Não há TTL, `expires_at` nem rotina de expurgo em `integrations_log` (só `created_at`). O **art. 15** determina o término do tratamento quando "os dados deixaram de ser necessários… ao alcance da finalidade específica" (inciso I); o **art. 16** exige que "os dados pessoais serão eliminados após o término de seu tratamento", salvo conservação para obrigação legal (inciso I) ou uso exclusivo anonimizado (inciso IV). Guardar payload com PII **para sempre** não se enquadra em nenhuma exceção do art. 16.

### 4.2 🔴 Excesso de armazenamento — art. 6º, III
O **art. 6º, III** (necessidade) limita o tratamento "ao mínimo necessário para a realização de suas finalidades… não excessivos". A finalidade de auditoria/diagnóstico/retry é atendida por metadados + identificador da entidade; **armazenar o `request_payload` e o `response_body` na íntegra, com CPF/CNH/documentos**, excede esse mínimo. O fato de o retry reler `log.request_payload` é uma escolha de conveniência — não uma necessidade que justifique persistir PII verbatim (o payload pode ser reconstruído a partir da entidade-fonte, ou armazenado mascarado/cifrado).

### 4.3 🔴 Segredo e segurança — art. 6º, VII + art. 46 e §2º
`curl_command`/`request_body` podem conter o header de autenticação do provider (`Authorization: Bearer …`). Persistir e **exibir isso na UI** viola o princípio de **segurança (art. 6º, VII)** e o dever de **medidas técnicas aptas a proteger… contra tratamento inadequado (art. 46)**, que devem existir **"desde a fase de concepção do produto… até a sua execução" (art. 46, §2º — privacy by design)**. Não há scrubbing/masking aplicado antes de gravar.

### 4.4 ⚠️ Exibição ampla na UI — art. 6º, III + art. 46
Expor `request_payload` + `response_body` a todo usuário com `IntegrationsAccessPermission` precisa passar no teste de **necessidade/need-to-know (art. 6º, III)** e **segurança (art. 46)**. Pode ser aceitável se forem os mesmos operadores que já enxergam os documentos do motorista — mas o default invasivo (mostrar tudo, sem máscara) contraria o privacy by design do art. 46, §2º.

---

## 5. Dado sensível 🚨 — art. 5º, II + art. 11 — flag **Parcial**

- **Confirmado:** `request_payload` contém **dado pessoal** (art. 5º, I) — CPF, nome, CNH.
- **A confirmar (Parcial):** se o payload carrega **dado pessoal sensível** (art. 5º, II — "dado referente à saúde"), o regime restrito do **art. 11** passa a valer (consentimento específico e destacado — art. 11, I — ou hipótese do art. 11, II). Os tipos de documento mapeados na integração (`DOCUMENT_TYPE_CHOICES`: cnh, mopp, nr_20, nr_35, crlv, cvv, cipp…) são, em sua maioria, **qualificação/habilitação**, não saúde stricto sensu. **Não confirmei** que ASO/exame médico ou outro dado de saúde entra nesse payload — o `request_body_template` é configurável por tenant e poderia incluir.
  - **O que falta:** inspecionar, num tenant real, o conteúdo de um `request_payload` de motorista para ver se há campo de saúde/aptidão. Se houver → achado de severidade alta (sensível persistido e exibido sem base do art. 11).

---

## 6. Transferência internacional — art. 33 — flag **Parcial/fora de escopo direto**

O `IntegrationLog` **em si** é gravado no Postgres do tenant (Brasil, presumido) — **não** faz transferência internacional. **Porém**, o *despacho* envia o `request_payload` para `provider.base_url`, que é configurável e **pode ser um ERP no exterior**. Se for, a **transferência** (não o log) precisa de base do **art. 33** (ex.: inciso VIII — consentimento específico e destacado para transferência; ou inciso IX c/c art. 7º). **Não sei** se algum tenant aponta `base_url` para fora do Brasil — verificar. (Escopo adjacente, registrado para não se perder.)

---

## 7. Tabela-resumo

| Dado tratado | Autorizado? | Base legal / Conflito (art. citado) |
|---|---|---|
| Metadados da chamada (event_type, status, status_code, retry, timestamps) | ✅ Sim | Legítimo interesse — art. 7º, IX + registro art. 37 |
| `entity_id` (UUID do motorista/veículo) | ✅ Sim | Necessário à finalidade de auditoria — art. 6º, III |
| Retry de log `failed` | ✅ Sim | Art. 7º, V/IX (continuidade do serviço) |
| `request_payload` completo (CPF, CNH, nome, docs) persistido | ❌ Não | Excesso — fere art. 6º, III (minimização) e art. 10, §1º |
| `response_body` completo do ERP | ⚠️ Parcial | Idem art. 6º, III — guardar só se necessário/mascarado |
| `curl_command`/`request_body` com token | ❌ Não | Vazamento de segredo — art. 6º, VII + art. 46/§2º |
| Retenção sem prazo de tudo acima | ❌ Não | Art. 15, I + art. 16 (eliminação) |
| Exibição de payload/response na UI a todos com permissão | ⚠️ Parcial | Need-to-know — art. 6º, III + art. 46 |
| Dado de saúde no payload (ASO) | ⚠️ A confirmar | Se houver: art. 11 (sem base = risco alto) |
| Envio do payload a `base_url` no exterior | ⚠️ A confirmar | Se houver: art. 33 (transferência internacional) |

---

## 8. Caminho de correção (ordem) — *corrigir o comportamento primeiro, documentar depois*

1. **(P0) Scrub de segredos antes de gravar.** Remover/mascarar `Authorization` e tokens do `curl_command`/`request_body`/headers antes de persistir o log. É o mais urgente — segredo hoje visível na UI. (art. 46)
2. **(P0/P1) Minimizar o payload persistido.** Gravar só o necessário para auditoria/retry; mascarar CPF/CNH em `request_payload`/`response_body` em repouso. Se o retry precisa do payload completo, **reconstruir a partir da entidade-fonte** em vez de guardar verbatim, ou **cifrar em repouso**. (art. 6º, III)
3. **(P1) Definir retenção + expurgo.** TTL para `integrations_log` (ex.: 90–180 dias) com job de purga; conservar além disso só sob obrigação legal (art. 16, I). (art. 15/16)
4. **(P1) Restringir a exibição na UI.** Mascarar payload/response por default; revelar só sob permissão mais estrita (need-to-know). (art. 6º, III + 46)
5. **(P2) Confirmar dado sensível** no payload real (saúde/ASO). Se houver, tratar sob art. 11 (base + scrubbing).
6. **(P2) Confirmar `base_url` no exterior.** Se houver, garantir base do art. 33 para a transferência.
7. **(P3) Documentar** no registro de operações (art. 37) / RoPA — **depois** de 1–4. Reescrever política **não** cria base legal nem conserta excesso de coleta.

---

## 9. Pontos a verificar (flags Parcial / Não sei)

- **Parcial** — conteúdo real do `request_payload` (há dado de saúde/ASO?). Inspecionar um log real de motorista.
- **Não sei** — algum `IntegrationProvider.base_url` aponta para servidor fora do Brasil?
- **Parcial** — existe DPA/instrução do controlador (tenant) sobre retenção de logs de integração? (relevante ao art. 39).

---

## 10. Referências cruzadas

- `Mudancas_AutoChecker_Relevantes_Observabilidade_AzureDevOps_2026-06-30.md` — contexto da mudança (PRs 15213/15214).
- `Etapa7_Analise_Consentimento_LGPD_Termo_vs_Sentry_AutoChecker.md` e `Etapa7_Auditoria_Conformidade_LGPD_Consentimento_vs_Scrubbing_AutoChecker.md` — caso análogo (Sentry): mesmo padrão de PII em telemetria.
- `reference/Lgpd.md` — texto oficial (fonte desta auditoria).
- Memória: `autochecker-etapa7-analise-lgpd`.

---

*Toda afirmação legal acima foi ancorada no texto de `reference/Lgpd.md`. Onde a base não foi confirmada na lei ou na evidência, usei flag **Parcial** ou **Não sei** — sem suposição.*
