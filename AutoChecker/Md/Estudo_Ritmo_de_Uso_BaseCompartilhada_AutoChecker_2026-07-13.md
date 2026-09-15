# Ritmo de Uso — Quando os clientes usam o AutoChecker (Tenant Base Compartilhada)

> **Fonte:** Grafana/Loki, `{job="autochecker-backend", environment="prod"}` filtrado por `tenant_schema="base_compartilhada"` e `user_email!=""` (só clientes reais). Série horária `count_over_time([1h])`, timestamps UTC → **BRT (UTC−3)**.
> **Janela:** 06–13/07/2026 (7 dias — retenção do Loki). **Gerado:** 13/07/2026.

## Resumo executivo

- **Pico:** 12–13h BRT (meio do expediente). **Janela ativa:** 08–20h. Fora disso o uso é ~zero.
- **O AutoChecker não é 24/7 — é um sistema de horário comercial.** Sobe às 8h, pica ao meio‑dia, cai após 18h, silencia à noite e no domingo.
- **Janela de manutenção/deploy segura: 22h–06h ou domingos** (uso ~zero) — agora comprovado por dado.
- O **pico do meio‑dia é ~4× o vale** — é ele que dimensiona a infraestrutura.
- **A base de clientes é majoritariamente paulista:** o feriado estadual de SP (09/07, Revolução Constitucionalista) **zerou** o tenant.

## 1. Heatmap da semana (hora × dia, BRT)

Requests de clientes reais por hora. Janela de 7 dias → cada dia da semana aparece uma vez (leia como a semana de 06–13/07, não "semana típica").

| Dia | 08h | 09h | 10h | 11h | 12h | 13h | 14h | 15h | 16h | 17h | 18h | 19h | 20h |
|---|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|--:|
| Seg 06/07 | 0 | 142 | 267 | 815 | **1317** | 1165 | 902 | 601 | 476 | 534 | 609 | 551 | 355 |
| Ter 07/07 | 297 | 463 | 565 | 456 | 771 | 610 | 582 | 427 | 306 | 400 | 211 | 48 | 0 |
| Qua 08/07 | 135 | 368 | 507 | 539 | 624 | 444 | 600 | 775 | 659 | 291 | 144 | 79 | 0 |
| **Qui 09/07** | 0 | 0 | 0 | 0 | 0 | 121 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | ← **feriado SP** |
| Sex 10/07 | 512 | **1150** | **1214** | 538 | 836 | 874 | 664 | 882 | 745 | 553 | 505 | 211 | 125 |
| Sáb 11/07 | 420 | 546 | 492 | 431 | 337 | 400 | 239 | 148 | 0 | 0 | 0 | 0 | 0 |
| Seg 13/07 | 61 | 158 | 100 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | ← parcial (manhã) |
| *Dom 12/07* | — | — | — | — | — | — | — | — | — | — | — | — | — | ← **zero (domingo)** |

**Quinta 09/07 zerada é achado, não erro.** É feriado estadual de SP. Confirmado que **não foi falha de log**: nesse dia o Loki ingeriu 1.825 linhas no total, mas só ~140 do Base Compartilhada, enquanto outros tenants seguiram com ~1.685. O domingo 12/07 também zerou; o **sábado 11/07 teve movimento** (parte dos clientes opera aos sábados).

## 2. Perfil por hora do dia (soma dos 7 dias)

| Hora | Tenant | Copercana | Rede Petro |
|--:|--:|--:|--:|
| 08h | 1.425 | 825 | 240 |
| 09h | 2.827 | 912 | 517 |
| 10h | 3.145 | 1.057 | 501 |
| 11h | 2.779 | 922 | 565 |
| **12h** | **3.885** | **1.075** | 652 |
| 13h | 3.614 | 750 | 788 |
| **14h** | 2.987 | 653 | **884** |
| 15h | 2.833 | 708 | 880 |
| 16h | 2.186 | 714 | 632 |
| 17h | 1.778 | 383 | 505 |
| 18h | 1.469 | 82 | 578 |
| 19h | 889 | 117 | 191 |
| **Total 7d** | **30.615** | 8.430 | 6.981 |

Madrugada (00–06h) e 21–23h: ~zero em todos.

## 3. Cada cliente tem seu relógio

| Cliente | Pico (BRT) | Janela | Perfil | Sábado? |
|---|---|---|---|---|
| **Tenant (todos)** | 12–13h | 08–20h | Expediente comercial clássico | parcial |
| **Copercana** | 10–12h | 08–17h | Operação de **manhã**, encerra cedo | **sim** |
| **Rede Petro** | 13–15h | 08–19h | Operação de **tarde**, vai até mais tarde | não |

Saber isso muda **quando avisar cada cliente** sobre manutenção e **como interpretar** uma queda de uso.

## 4. Por que importa (uso operacional)

- **🛠️ Manutenção & deploy:** uso ~zero em 22h–06h e domingos → janela natural para deploy, migração e reinício de serviços com impacto mínimo.
- **📟 Alertas com baseline por hora:** queda a zero às 14h de dia útil = incidente; a mesma queda às 3h ou no domingo = normal. Sem esse perfil, alerta de "queda de tráfego" dá falso positivo toda madrugada e fim de semana.
- **👥 Suporte/plantão:** demanda vive em 08–19h → não precisa 24/7.
- **📈 Capacidade/custo:** pico do meio‑dia ~4× o vale dita o dimensionamento; folga enorme à noite para jobs pesados (reprocessamento, relatórios).

## 5. Método & limitações

- Timestamps UTC convertidos para **BRT (UTC−3)**. Clientes por domínio de e‑mail (`|= "redepetro"`, `|= "copercana"`).
- **Retenção do Loki ≈ 7 dias** → retrato de **uma semana**; dia‑da‑semana coincide com data específica (por isso a quinta = feriado distorce o "perfil de quinta"). Para padrão semanal estável, acumular semanas num dashboard fixo.
- O volume é dominado por polling de fundo, mas como o polling só ocorre **com o app aberto**, ele é um bom marcador de **presença** — que é o que este estudo mede.

## 6. Próximos passos

1. **Fixar este heatmap num painel do Grafana** acumulando semanas — supera a retenção de 7 dias.
2. **Definir a janela de deploy/manutenção oficial** (22h–06h ou domingo) com base neste dado.
3. **Configurar alertas de volume com baseline por hora/dia** — elimina falso positivo noturno/fim de semana.
4. **Cruzar com calendário de feriados estaduais (SP)** ao interpretar quedas — a base é paulista.

---
*Parte da série de estudos de uso do AutoChecker. Complementa "Uso de Telas e Funções — Base Compartilhada" (13/07/2026).*
