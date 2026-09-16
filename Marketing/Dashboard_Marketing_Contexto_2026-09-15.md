# Dashboard de Marketing — AutoMind

## Contexto

Wladimir (liderança, encerrando participação oficial no projeto) propôs uma estrutura de 4 dashboards de acompanhamento mensal:

1. Vendas donos de carga
2. Vendas transportadora
3. **Marketing** (escopo deste documento)
4. Backlog de inovação (estático, só registro do que existe no backlog)

Responsável por ajustar e evoluir o dashboard de marketing: Jaquian (liderança de marketing).

## Glossário

- **HT (Human Track):** vendas conduzidas por pessoas, vendedor falando diretamente com o cliente.
- **DT (Digital Track):** vendas/leads gerados por marketing digital (site, landing pages, conteúdo). Foco principal do setor de marketing.
- **Funil de vendas (etapas):** contacted → accepted → tested (fez o teste do produto) → consideration → assinatura.
- **ABM (Account-Based Marketing):** prospecção mirando empresas específicas.

## Estrutura proposta do dashboard de marketing

### 1. Produtividade
O que marketing produziu no mês (posts, materiais, campanhas, webinars, ações de comunidade etc.), destacando:
- O que foi direcionado ao **DT**.
- O que foi apoio à **HT**.
- Campo de "destaque do mês" para justificar quedas de produção (ex: mês de evento como Expopostos consumiu a capacidade da equipe).

### 2. Performance
Indicadores-chave por categoria produzida, com comparativo mês a mês e espaço para destacar o item de melhor resultado no período.

Métricas centrais:
- **Acessos ao site/landing pages** (site institucional está sendo remodelado em Next.js; espera-se que as ações de marketing tragam tráfego pra lá e pras LPs de produto).
- **Métrica prioritária (2.5):** quantos cadastros de teste (trial) vieram do DT, e quantos desses de fato realizaram o teste do produto. Status atual: zerado. Wladimir marcou essa como a métrica mais importante do dashboard inteiro.

## Pendências / o que falta cobrir

O rascunho de Wladimir não é 100% completo. Falta incorporar:
- [ ] Webinars
- [ ] Ações de comunidade
- [ ] Qualquer outra atividade sob liderança do Jaquian que hoje não está listada

Objetivo final reforçado por Wladimir: marketing não deve ser área de "produção de posts", mas de conteúdo e ações estratégicas que conduzam o cliente pelo funil até o teste (consideration), pensando em escala (sabendo que a escala do HT é mais limitada).

## Referência

- Vendas donos de carga e vendas transportadora usam a mesma planilha base do funil (Human Track).
- Base Compartilhada não entra no dashboard porque já é considerada vendida (assim que assinar contrato, passa a contar como 1 assinatura / R$ 2.200/mês).

---

## Fontes de dados — de onde sai cada número do dashboard

Levantamento de 15/09/2026, cruzando o bloco `DADOS` do protótipo (`Html/Dashboard_Marketing_AutoMind_2026-09-15.html`) com o que já está documentado no repositório. Os números do protótipo são **ilustrativos**; este mapa diz o que precisa existir para substituí-los por dados reais.

Resumo: quase nada do dashboard tem fonte automática hoje. A maior parte vem de ferramentas externas de marketing ou de planilha manual. O único trecho com telemetria própria é o funil de trial do AutoChecker — e mesmo esse está incompleto (não registra origem do cadastro).

### 1. Produtividade (`producao.{categoria}.{dt,ht}`)

| Fonte | Status |
|---|---|
| **Planilha de produção do marketing** (responsável: Jaquian) — uma linha por peça: data, categoria, DT ou HT, link | **Não existe ainda.** Precisa ser criada. É lançamento manual por natureza: nenhuma ferramenta sabe se um post foi "apoio ao HT". |

### 2. Acessos (`acessos.site`, `acessos.lps`)

| Fonte | Status |
|---|---|
| Analytics do site Next.js novo (GA4 / Vercel Analytics / Plausible) | Depende do que o dev instalou no site remodelado. **Confirmar com dev qual ferramenta está ativa.** |
| LPs de produto | Se estiverem em ferramenta separada (RD Station, Webflow etc.), cada uma tem seu painel. |

### 3. Performance por categoria (`perf.{categoria}.v` e `best`)

| Categoria | Indicador | De onde sai |
|---|---|---|
| posts | Alcance | Instagram / LinkedIn Insights — export mensal |
| email | Taxa de abertura | **Brevo** — a AutoMind já usa Brevo (adapter de e-mail do AutoChecker e monitor de custos). Se a newsletter sai de lá, o relatório de campanha dá abertura e clique direto. |
| camp | Cliques | Meta Ads / Google Ads |
| lp | Conversão em cadastro | cadastros ÷ acessos da LP — cruza o item 2 com o item 4 |
| webinar | Presentes | Plataforma do webinar (Zoom / Meet / YouTube) — pendência do contexto, ainda não definida |
| comun | Participantes ativos | Manual (grupo WhatsApp / LinkedIn) — pendência do contexto |
| mat / abm | Usados em propostas / reuniões geradas | Planilha do funil HT (a mesma dos dashboards de Vendas) |

Tudo aqui é export manual mensal para a planilha. Não vale automatizar antes de o processo existir.

### 4. Funil (`funil.{cadastros,testaram,consideration,assinatura}`) — métrica prioritária (2.5)

| Etapa | Fonte que existe | O que falta |
|---|---|---|
| **cadastros** (trials vindos do DT) | AutoChecker tem o app `backend/apps/trial` e o endpoint `/api/trial/status/` (`is_trial`, expiração, quota de 50 uploads). `AutoChecker/Md/Inventario_Tenants_Trials_AutoChecker_2026-07-27.md` já lista trials ativos via Loki. | **Origem do cadastro não é registrada.** Não dá para dizer se um trial veio de LP, anúncio ou vendedor. A métrica está "zerada" porque ninguém sabe de onde o cadastro veio, não porque ninguém se cadastra. |
| **testaram** | Já observável: `Uploads usados X/50` no Loki (o inventário mostrou Tecab com 0/50 — trial que não engatou). Definição: "testou" = ≥ 1 upload no período de trial. | Nada — extraível hoje com a mesma query do inventário. |
| **consideration / assinatura** | Planilha do funil HT (contacted → accepted → tested → consideration → assinatura), mantida por Vendas. | Coluna "origem DT/HT" para filtrar só o que veio do digital. |

> ⚠️ Isso cobre **só o AutoChecker**. AutoLoad e AutoMed não têm fluxo de trial self-service (nada no repositório indica o contrário), então o funil digital deles é zero por definição, não por falta de medição.

### O que precisa acontecer, em ordem

1. **Dev — atribuição no cadastro de trial (AutoChecker):** capturar `utm_source` / `utm_medium` / `utm_campaign` e `referrer` no formulário de trial e persistir no tenant. Sem isso a métrica 2.5 não sai de forma confiável. É a única dependência de desenvolvimento real desta lista.
2. **Interino, até o item 1:** cruzar manualmente e-mails de novos trials (Loki / inventário) com submissões das LPs e cliques de campanha. Trabalhoso, mas destrava o número já no primeiro mês.
3. **Marketing — planilha de produção** com DT/HT por peça (seção 1) e aba de performance com o export mensal de cada ferramenta (seção 3).
4. **Vendas — coluna "origem"** na planilha do funil HT, para consideration/assinatura filtráveis por DT.
5. **Confirmar com dev qual analytics está no site Next.js novo** e nas LPs.

Depois disso, o dashboard vira leitura de duas planilhas + uma query Loki por mês — e só então faz sentido automatizar (ex.: o dash lendo um Google Sheet em vez do bloco `DADOS` hardcoded).

### Perguntas em aberto

**Para o dev**
- Qual analytics está instalado no site Next.js novo e nas LPs?
- O formulário de trial do AutoChecker consegue receber e gravar UTM/referrer? Onde ficaria (model do tenant, `apps/trial`)?
- A newsletter sai pelo Brevo ou por outra ferramenta?

**Para o Jaquian**
- Quais ferramentas estão em uso hoje para posts, anúncios, e-mail e webinar (para saber de onde exportar)?
- Existe alguma planilha de produção atual que possa virar a base da seção 1?
- Como contar "participantes ativos" de comunidade — qual canal, qual critério?
