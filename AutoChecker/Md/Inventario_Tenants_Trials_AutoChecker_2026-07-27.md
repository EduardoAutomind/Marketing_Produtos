Levantamento **ao vivo** do Loki (janela de 30 dias), extraído em **27/07/2026 19:57 (BRT)** pelo motor do Checker Monitor (`/api/fleet`). Objetivo: **inventariar todos os tenants** do AutoChecker e **separar quem está em trial de quem não está**.

> ⚠️ **Confidencial · uso interno AutoMind.** Contém nomes de clientes e dados de uso. Não distribuir fora da gestão.

---

## Panorama

| Métrica | Valor |
|---|---:|
| Tenants no total (30d) | **25** |
| Tenants de **cliente** | **14** |
| Tenants **internos** (AutoMind / QA / suporte / demo) | 11 |
| Clientes que só aparecem no **worker** (integração/API, sem login web) | 10 |
| Tenants em **trial ativo** | **1** (Tecab) |

O tráfego segue concentradíssimo: a **Base Compartilhada** (multiempresa) responde por praticamente todo o uso web e a maior fatia do worker. A maioria dos demais clientes só toca o produto pela **integração/API** (fila do worker Celery), sem sessão de tela.

---

## 1. Tenants de CLIENTE (14)

Ordenados por volume total (web + worker) na janela de 30 dias.

| # | Tenant | Canal | Requisições web | Tarefas worker | Situação |
|--:|---|:--:|--:|--:|---|
| 1 | **Base Compartilhada** | both | 116.715 | 31.463 | Produção — núcleo multiempresa (~85% do uso) |
| 2 | **Tecab** | both | 2.895 | 184 | 🟡 **TRIAL ATIVO** |
| 3 | Logum Logística S.A. | worker | 0 | 1.896 | Só integração/API |
| 4 | Unibras | worker | 0 | 1.896 | Só integração/API |
| 5 | Atvos Bioenergia | worker | 0 | 576 | Só integração/API |
| 6 | Idaza | worker | 0 | 492 | Só integração/API |
| 7 | Watt Distribuidora de Combustíveis | worker | 0 | 344 | Só integração/API |
| 8 | PetroRio | worker | 0 | 260 | Só integração/API |
| 9 | Guterres Comércio de Combustíveis | both | 187 | 70 | Produção |
| 10 | Vopak | worker | 0 | 164 | Só integração/API |
| 11 | Ciapetro | worker | 0 | 112 | Só integração/API |
| 12 | Atvos | worker | 0 | 108 | ⚠️ Suspensa, mas ainda processando (fantasma) |
| 13 | Ultracargo Logística | both | 14 | 60 | Produção |
| 14 | Petroserra | worker | 0 | 36 | Só integração/API |

---

## 2. Trial × Não-trial

A flag de trial é lida do endpoint web `/api/trial/status/` (campo `is_trial` no último retrato de cada tenant na janela).

### 🟡 Em trial ativo — 1 tenant

| Tenant | is_trial | Expira | Dias restantes | Uploads usados | Alerta |
|---|:--:|:--:|:--:|:--:|:--:|
| **Tecab** | `true` | **02/08/2026** | 9 | **0 / 50** | normal |

> 🟡 **Tecab está em trial e ainda não usou nada** (0 de 50 uploads), a 9 dias de vencer. Mesmo padrão da leitura anterior (22/07): trial que não engatou. Vale um contato comercial/CS antes de 02/08 — senão expira sem nenhuma experiência de produto.

### ✅ Não-trial — 13 tenants de cliente

Os demais 13 tenants de cliente **não** retornam `is_trial:true` — são contas de produção/pagas. Os tenants internos (AutoMind, QA, suporte, demonstração) também não são trial.

### ⚠️ Ressalva de método (importante)

A flag de trial vem de um endpoint **web**. Os **10 tenants que só aparecem no worker** (Logum, Unibras, Atvos Bioenergia, Idaza, Watt, PetroRio, Vopak, Ciapetro, Atvos, Petroserra) **nunca chamam** `/api/trial/status/` — logo, não há flag lida diretamente para eles; eles simplesmente não aparecem como trial. Pela natureza (integração/API contínua em volume), são quase certamente **produção**, mas isso é inferência, não a flag. Confirmação nominal tenant-a-tenant é possível, porém mais lenta (varredura por tenant no Loki).

---

## 3. Sinais de atenção

| Sinal | Detalhe |
|---|---|
| 👻 **Atvos processando suspensa** | O tenant `atvos` está marcado como suspenso, mas ainda registrou **108 tarefas** no worker em 30d — deveria estar em 0. Investigar por que a integração continua ativa. |
| 🔇 **Transportadora Providência silenciou** | Tinha **20 requisições** na janela anterior (30–58 dias atrás) e caiu para **0** agora. Cliente sumiu — vale checar se churnou ou só pausou. |
| 🟡 **Tecab (trial) sem primeiro uso** | 0/50 uploads a 9 dias do fim do trial. |

---

## 4. Tenants internos (não são cliente)

Listados para transparência do inventário — **não** entram na contagem de clientes nem de trials.

| Tenant | Canal | Web | Worker |
|---|:--:|--:|--:|
| Suporte | web | 3.521 | 0 |
| AutoMind V2 | web | 2.928 | 0 |
| AutoMind | both | 2.636 | 984 |
| Portal de Gestão (`public`) | web | 1.161 | 0 |
| AutoMind QA | web | 1.003 | 0 |
| AutoMind (`_2_dc8b63db`) | both | 806 | 63 |
| Demonstração Comercial | both | 52 | 1.724 |
| Mobile | web | 339 | 0 |
| Time Suporte (`eduardo_santos`) | web | 185 | 0 |
| AutoMind (teste) | both | 60 | 13 |
| Tarcisiosa | worker | 0 | 12 |

---

### Notas técnicas

- **Fonte:** logs de produção do AutoChecker no Grafana/Loki (`app="backend"` para web; `job="celery-tasks", status="started"` para worker). Datasource Loki confirmado saudável no momento da extração.
- **Janela:** 30 dias corridos até 27/07/2026 19:57 BRT. "Inativos/silenciaram" compara com a janela anterior (30–58 dias atrás).
- **Contagens** = nº de linhas de log (requisições web / tarefas iniciadas no worker), não nº de documentos nem de usuários únicos.
- **Trial:** último `is_trial` observado por tenant via `/api/trial/status/`; trials já expirados podem ter virado `is_trial:false` e não aparecem aqui.
