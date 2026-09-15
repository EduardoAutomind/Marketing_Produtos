# Etapa 7 — Remediação: Fechamento dos Achados de PII na Telemetria

> **Cronograma de Observabilidade · AutoChecker · Onda 0 (Saneamento da Base — GATE)**
> `Objeto: sair do diagnóstico e ENTREGAR a correção exata de cada achado de PII já mapeado — patch pronto, quem executa, como verificar.`
> `Gerado: 2026-07-06 · Confiança: Sei (citações revalidadas contra o código de hoje) · Sucessor operacional do Estudo de Soluções de 30/06`

| | |
|---|---|
| **Produto** | AutoChecker (frontend `AutoChecker_Frontend`, serviço `AutoChecker_Custos`, backend/worker `AutoChecker`) |
| **Pergunta** | Os achados de PII da Etapa 7 estão diagnosticados à exaustão. **Como fechá-los?** Qual o patch exato, quem aplica e como confirmar que fechou? |
| **Fontes** | Código real em `Produtos/Autochecker/**` (`arquivo:linha`, lido 06/07/2026) · Estudo de Soluções 30/06 (camadas A–F) · Playbook de Data Scrubbing (painel) · `Lgpd.md` (Lei nº 13.709/2018) |

---

## Em uma frase

Restam **3 achados de PII abertos** (revalidados hoje, zero progresso no código): (1) `sendDefaultPii: true`, (2) e-mail no `Sentry.setUser`, (3) `IntegrationLog` com payload cru sem retenção exposto na UI. Abaixo cada um vem com o **patch literal**, a **verificação** e o **ticket pronto para abrir** — separando o que **você faz sozinho hoje** (painel Sentry + abrir tickets) do que **depende do dev** (os 3 patches de código).

---

## Placar dos achados (06/07/2026)

| # | Achado | Local (revalidado hoje) | Vetor legal | Quem corrige | Esforço |
|---|---|---|---|---|---|
| **1** | `sendDefaultPii: true` — **causa-raiz** | `AutoChecker_Frontend/instrumentation-client.ts:21`, `sentry.server.config.ts:16`, `sentry.edge.config.ts:17` + `AutoChecker_Custos/src/instrument.ts:12` | art. 6º III (minimização), art. 11, art. 33 | 👨‍💻 dev | **P** (trivial) |
| **2** | E-mail identificável no `setUser` | `AutoChecker_Frontend/modules/auth/hooks/useAuth.tsx:175` (login) e `:388` (selectTenant) | art. 6º III (minimização) | 👨‍💻 dev | **P** (trivial) |
| **3** | `IntegrationLog` — payload cru, sem TTL, exposto na UI | `shared/models/integrations.py:778,794` · `backend/apps/integrations/serializers.py:401` · `worker/config/celery.py:69` (sem expurgo) | art. 6º III, art. 15/16 (retenção), art. 46 §2º | 👨‍💻 dev + ⚖️ DPO | **M** |

> **Nota de escopo resolvida:** o achado antigo *"qual frontend é o de produção?"* (#7) fechou por si — o monorepo `AutoChecker/frontend/` foi **deletado do repo real em 29/06** (a cópia local é resíduo); o canônico é `AutoChecker_Frontend`. Por isso os "5 pontos" de `sendDefaultPii` viraram **4 pontos vivos** (3 no front + 1 no Custos). Não corrija a pasta legada.

---

## Achado 1 — `sendDefaultPii: true` (causa-raiz) · 👨‍💻 dev

**Por que é o nº 1:** com `true`, o SDK anexa **IP, cookies, headers e corpos de request/response** a cada evento — é por esse canal que CPF/CNH/ASO **em trânsito** chega ao Sentry (SaaS no exterior). Desligar corta o vetor dominante. O Session Replay já mascara texto e bloqueia mídia por default no `@sentry/nextjs ^10.43.0` — **não** é a manchete; o `sendDefaultPii` é.

### Patch (4 arquivos, 1 linha cada)

**`AutoChecker_Frontend/instrumentation-client.ts:21`**
```diff
-  sendDefaultPii: true,
+  sendDefaultPii: false,
```

**`AutoChecker_Frontend/sentry.server.config.ts:16`** — *runtime que mais processa documento; prioridade máxima*
```diff
-  sendDefaultPii: true,
+  sendDefaultPii: false,
```

**`AutoChecker_Frontend/sentry.edge.config.ts:17`**
```diff
-  sendDefaultPii: true,
+  sendDefaultPii: false,
```

**`AutoChecker_Custos/src/instrument.ts:12`**
```diff
-  sendDefaultPii: true,
+  sendDefaultPii: false,
```

### Rede de segurança na origem (recomendado junto — A3 do estudo)
Mesmo com `sendDefaultPii: false`, adicionar um `beforeSend` que remove campos sensíveis do que sobrar (ex.: erro que carrega body no `extra`). No `Sentry.init` dos 3 configs do front:
```ts
  beforeSend(event) {
    // Remove corpos/headers que possam carregar PII de negócio
    if (event.request) {
      delete event.request.cookies;
      delete event.request.data;      // request body
      if (event.request.headers) {
        delete event.request.headers["authorization"];
        delete event.request.headers["cookie"];
      }
    }
    return event;
  },
```

### Como verificar que fechou
1. Rodar em staging, disparar um erro numa rota que processa documento.
2. No Sentry, abrir o evento → aba **Request**: não deve haver `cookies`, `headers` de auth nem `data` (body). O contexto `user` não deve trazer IP.
3. Confirmar que a versão que **builda em produção** é a com o patch (não um lockfile/cache antigo).

---

## Achado 2 — E-mail no `Sentry.setUser` · 👨‍💻 dev

**Problema:** `Sentry.setUser({ id, email })` carimba o e-mail (PII identificável) em **todo** evento do usuário. O `id` já basta para correlação. Fere minimização (art. 6º III).

### Patch (2 linhas, mesmo arquivo)

**`AutoChecker_Frontend/modules/auth/hooks/useAuth.tsx:175`** (pós-login)
```diff
-        Sentry.setUser({ id: String(response.user.id), email: response.user.email });
+        Sentry.setUser({ id: String(response.user.id) });
```

**`AutoChecker_Frontend/modules/auth/hooks/useAuth.tsx:388`** (pós-selectTenant)
```diff
-        Sentry.setUser({ id: String(userResponse.data.id), email: userResponse.data.email });
+        Sentry.setUser({ id: String(userResponse.data.id) });
```

> As tags `schema_name`/`tenant_name` (`:389–390`) e o `Sentry.setUser(null)` do logout (`:224`) permanecem — não são PII de titular.

### Como verificar
No Sentry, abrir um evento de usuário logado → seção **User**: deve aparecer só `id`, sem `email`.

---

## Achado 3 — `IntegrationLog`: payload cru, sem retenção, exposto na UI · 👨‍💻 dev + ⚖️ DPO

Três problemas distintos no mesmo modelo — e uma **armadilha**: a ação `retry` (`views.py:375`) **re-despacha usando `log.request_payload` cru** (`entity_data=log.request_payload`). **Logo NÃO se pode mascarar/apagar o payload no banco** sem quebrar o retry. A correção correta ataca cada camada no lugar certo:

### 3a — Parar de EXPOR o payload/response cru na UI (P0, não quebra retry)
Mascarar na **saída do serializer** (a UI deixa de mostrar CPF/CNH/token; o dado no banco continua íntegro para o retry).

**`backend/apps/integrations/serializers.py`** — trocar os campos crus por versões mascaradas no `IntegrationLogDetailSerializer`:
```python
import re

# Chaves cujo VALOR deve ser mascarado (superset do api_logging: inclui cnh, rg, aso, email, nome...)
_PII_KEYS = re.compile(
    r"password|token|secret|cpf|cnpj|cnh|rg|aso|email|nome|name|phone|telefone|"
    r"endereco|address|birth|nascimento|senha|auth",
    re.IGNORECASE,
)

def _scrub(value):
    """Mascara valores de chaves sensíveis, recursivamente. Não muta o original."""
    if isinstance(value, dict):
        return {k: ("***" if _PII_KEYS.search(k) else _scrub(v)) for k, v in value.items()}
    if isinstance(value, list):
        return [_scrub(v) for v in value]
    return value


class IntegrationLogDetailSerializer(serializers.ModelSerializer):
    provider_display_name = serializers.CharField(
        source="provider.display_name", read_only=True
    )
    request_payload = serializers.SerializerMethodField()
    response_body = serializers.SerializerMethodField()

    def get_request_payload(self, obj):
        return _scrub(obj.request_payload)

    def get_response_body(self, obj):
        # response_body é TextField (str); mascarar por regex de valor conhecido (CPF/e-mail)
        text = obj.response_body or ""
        text = re.sub(r"\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b", "***CPF***", text)
        text = re.sub(r"[\w.+-]+@[\w-]+\.[\w.-]+", "***EMAIL***", text)
        return text

    class Meta:
        model = IntegrationLog
        fields = [ ... ]   # inalterado
```
> Restringir também **quem** vê o detalhe: hoje o `IntegrationLogViewSet` exige só `IsAuthenticated, IsSubscriber`. Avaliar limitar o *detail*/`retry` a admin do tenant (permissão dedicada).

### 3b — Definir RETENÇÃO / expurgo (fecha art. 15/16) · dev
Não há **nenhuma** task de limpeza no `beat_schedule`. Adicionar uma:

**`shared/tasks/integration_tasks.py`** (nova task):
```python
@shared_task
def purge_old_integration_logs(days: int = 90):
    """Expurga IntegrationLog além da janela de retenção (LGPD art. 15/16)."""
    from django.utils import timezone
    from datetime import timedelta
    from shared.models.integrations import IntegrationLog
    cutoff = timezone.now() - timedelta(days=days)
    deleted, _ = IntegrationLog.objects.filter(created_at__lt=cutoff).delete()
    return {"deleted": deleted, "cutoff": cutoff.isoformat()}
```

**`worker/config/celery.py`** — registrar no `beat_schedule` (junto das demais, ~linha 105):
```python
    "purge-old-integration-logs-daily": {
        "task": "shared.tasks.integration_tasks.purge_old_integration_logs",
        "schedule": crontab(hour=1, minute=0),
        "options": {"queue": "admin_tasks"},
    },
```
> A janela (90 dias) é sugestão — **o DPO define** com base na finalidade real (troubleshooting de integração). Documentar a decisão.

### 3c — Minimizar/cifrar o payload EM REPOUSO (decisão estrutural) · dev + DPO
Como o `retry` precisa do payload, as opções (escolher com o DPO):
- **Cifra em repouso** do `request_payload`/`response_body` (ex.: `django-cryptography` / `EncryptedJSONField`) → retry decifra, UI mostra mascarado, banco fica ilegível a quem acessar o dump. **Recomendado.**
- **Minimizar no persist**: gravar só os campos necessários ao retry (remover documentos/imagens embutidos), mantendo referência por ID. Menor esforço, protege menos.
- **TTL curto (3a+3b)** como mitigação temporal enquanto a cifra não entra.

### Como verificar
1. **3a:** `GET` no detail de um log com CPF no payload → resposta traz `***`, não o valor.
2. **3b:** rodar `purge_old_integration_logs(days=0)` em staging com um log antigo → conta como deletado; confirmar entrada no beat.
3. Retry de um log `failed` continua funcionando (usa o valor cru do banco, não o mascarado da UI).

---

## O que VOCÊ faz sozinho HOJE (sem depender do dev) · 🧍

Enquanto os 3 patches esperam o dev, a **Camada 3 (painel Sentry)** avança a Etapa 7 por conta própria — é rede de segurança na ingestão. Passo a passo detalhado no **Playbook de Data Scrubbing** (`Etapa7_Playbook_DataScrubbing_Painel_Sentry_8Projetos_2026-06-30.md`). Em resumo:

1. **Advanced Data Scrubbing** (Settings → Security & Privacy) org-wide: regras para CPF/CNPJ/e-mail, `$message`, `extra.**`, `request.**`.
2. **"Prevent Storing of IP Addresses"** ligado + regra `$user.geo.**`.
3. **Data retention** no menor valor do plano (minimização temporal).
4. **Purga do pretérito** (eventos/replays já gravados em desconformidade) — **com o DPO** (art. 16 + 18 IV).

> ⚠️ O token do Sentry MCP é **read-only** (`update_issue`/config dão 403), então esses passos são **manuais no painel** — não dá para automatizar via ferramenta. Comunicar honestamente ao gestor: *"camada server-side aplicada por mim; correção de origem (patches 1–3) pendente no código, depende do dev."*

---

## Tickets prontos para abrir (Azure Boards) · 🧍 você cria, dev/DPO recebem

> Feature-pai da Etapa 7: **#40531**. Sugiro 3 filhos:

**TICKET A — `[Etapa 7] Sentry: sendDefaultPii=false + setUser só id + beforeSend` (dev)**
- **Tipo/Esforço:** Task / 1–2 pts.
- **Descrição:** Corrigir os 4 pontos de `sendDefaultPii: true` (`AutoChecker_Frontend` client/server/edge + `AutoChecker_Custos/src/instrument.ts:12`) para `false`; remover `email` dos 2 `Sentry.setUser` (`useAuth.tsx:175,388`); adicionar `beforeSend` de scrub nos 3 configs do front.
- **Critério de aceite:** evento de erro em staging não traz cookies/headers-auth/body na aba Request; seção User traz só `id`; build de produção confirmado.

**TICKET B — `[Etapa 7] IntegrationLog: mascarar UI + retenção + cifra em repouso` (dev + DPO)**
- **Tipo/Esforço:** Task / 3–5 pts.
- **Descrição:** Mascarar `request_payload`/`response_body` no `IntegrationLogDetailSerializer`; criar `purge_old_integration_logs` + beat diário; avaliar cifra em repouso; restringir detail/retry a admin do tenant. **Atenção:** `retry` usa o payload cru — não mascarar no banco.
- **Critério de aceite:** detail retorna `***` no payload; task de expurgo no beat; retry de log `failed` segue funcional; janela de retenção decidida com DPO e documentada.

**TICKET C — `[Etapa 7] Governança: retenção, purga pretérita, DPA/SCC` (DPO)**
- **Tipo/Esforço:** Task / a definir.
- **Descrição:** Definir janela de retenção do IntegrationLog e dos eventos Sentry; decidir purga do pretérito (art. 16/18 IV) e reporte de incidente (art. 48); confirmar DPA/SCC com o Sentry (art. 33); **só depois** atualizar Termo/Política (transparência do tratamento mínimo).

---

## Ordem de execução

| Fase | O quê | Quem | Depende de |
|---|---|---|---|
| **P0 — hoje** | Camada 3 no painel (scrubbing/IP/retention) + abrir Tickets A/B/C + alinhar purga pretérita c/ DPO | 🧍 você + ⚖️ | nada |
| **P1 — dev, alto impacto/baixo esforço** | Ticket A (achados 1+2) → depois 3a+3b do Ticket B | 👨‍💻 | PR aprovado |
| **P2 — estrutural/jurídico** | 3c (cifra em repouso), Ticket C, e só então Termo/Política | 👨‍💻 + ⚖️ | decisão DPO |

> **Regra inegociável (já auditada):** atualizar Termo/Política vem **por último**. Documento ajusta transparência; a minimização (patches 1–3 + painel) ajusta a **legalidade**. Reescrever a política não torna lícito coletar dado excessivo.

---

## Flags de confiança

| Afirmação | Flag |
|---|---|
| Os 4 pontos de `sendDefaultPii:true` e as 2 linhas de `setUser` estão nos locais citados | **Sei** (lido 06/07) |
| `retry` usa `request_payload` cru → não mascarar no banco | **Sei** (`views.py:375`) |
| Não há task de expurgo do IntegrationLog no beat | **Sei** (`celery.py:69–111`) |
| `api_logging._sanitize_payload` só cobre `password\|token\|secret\|cpf\|cnpj` por chave, e loga `user_email` cru | **Sei** (`api_logging.py:8,57,113`) |
| Replay v10 mascara texto/bloqueia mídia por default (residual: canvas/unmask/build) | **Sei / Parcial** (reverificar canvas) |
| Cifra em repouso é a melhor opção para 3c | **Parcial** — validar liblib/esforço com o dev |
| Existe DPA/SCC firmado com o Sentry | **Não sei** — DPO confirma |
| Janela de retenção adequada (sugerido 90d) | **Não sei** — DPO define pela finalidade |

---

## Fontes

1. Código — `AutoChecker_Frontend/instrumentation-client.ts:21`, `sentry.server.config.ts:16`, `sentry.edge.config.ts:17`; `AutoChecker_Custos/src/instrument.ts:12`; `modules/auth/hooks/useAuth.tsx:175,388` — lidos 06/07/2026.
2. Código — `shared/models/integrations.py:734–840` (IntegrationLog); `backend/apps/integrations/serializers.py:378–424`; `backend/apps/integrations/views.py:326–392` (retry usa payload cru); `worker/config/celery.py:69–111` (beat sem expurgo); `backend/config/middleware/api_logging.py:8,57,107–117` (scrub parcial por chave).
3. Estudo de Soluções — `Etapa7_Estudo_Solucoes_Dados_Sensiveis_AutoChecker_2026-06-30.md` (camadas A–F, matriz, P0/P1/P2).
4. Playbook — `Etapa7_Playbook_DataScrubbing_Painel_Sentry_8Projetos_2026-06-30.md` (execução da Camada 3).
5. Auditoria LGPD — `Etapa7_Auditoria_Conformidade_LGPD_Consentimento_vs_Scrubbing_AutoChecker.md`; `Auditoria_LGPD_IntegrationLog_AutoChecker_2026-06-30.md`.
6. `Lgpd.md` — Lei nº 13.709/2018 (edição Senado, jun/2024): art. 6º I/III, art. 11, art. 15, art. 16, art. 18 IV, art. 33, art. 46 §2º, art. 48.

---

### Referências cruzadas
- **Estudo de Soluções (30/06)** — este documento é o passo operacional das camadas A1/A2/A3/C1–C4/F.
- **Playbook Data Scrubbing** — detalha o P0 que você executa sozinho.
- **Etapa 5** (consolidar `init_sentry`) — onde fixar `send_default_pii=False` explícito no backend.
- **Memórias:** `autochecker-etapa7-analise-lgpd`, `autochecker-integrationlog-observabilidade-lgpd`, `sentry-token-readonly`, `autochecker-trabalho-autonomo-vs-dev`.
</content>
</invoke>
