<div class="kpis" markdown="1">
<div class="kpi"><div class="n">19</div><div class="l">Tenants ativos (12 cliente + 7 internos)</div></div>
<div class="kpi"><div class="n">12</div><div class="l">Empresas usam pela Base Compartilhada</div></div>
<div class="kpi"><div class="n">97,7 mil</div><div class="l">Requisições de clientes · ~905 h</div></div>
<div class="kpi bad"><div class="n">89,5%</div><div class="l">Do tráfego é polling, não pessoa</div></div>
</div>

> ⚠️ **Confidencial — uso interno.** Contém nomes e métricas de clientes. Janela: **20/06 a 20/07/2026** (30 dias). Fonte: Grafana/Loki + Sentry, extração de 20/07.

Este painel reúne o que já conseguimos afirmar sobre os clientes do AutoChecker **sem depender do time de desenvolvimento** — tudo sai da telemetria que já existe (Loki + Sentry). Cada seção traz a pergunta de negócio, o número real e a ação sugerida para a gestão.

# 1. Ranking de clientes por uso

Quem sustenta a operação e quem está no radar. Ordenado por **tempo de uso** (proxy — janelas de 30 min ativas). Todas as empresas operam dentro da Base Compartilhada.

| # | Empresa | Tempo | Requisições | Usuários | Uploads | Erro |
|---|---------|------:|------------:|---------:|--------:|-----:|
| 1 | **Copercana** | 503,0 h | 58.462 | 6 | 135 | 0,70% |
| 2 | Rede Petro | 119,0 h | 15.280 | 4 | 68 | 0,04% |
| 3 | Flexpetro | 84,5 h | 5.803 | 1 | 62 | 0,09% |
| 4 | Setta Combustíveis | 45,5 h | 3.713 | 1 | 22 | 0,00% |
| 5 | Larco Petróleo | 40,5 h | 4.091 | 2 | 16 | **5,89%** |
| 6 | Biopetro | 39,0 h | 4.387 | 2 | 24 | 0,82% |
| 7 | Small | 38,0 h | 3.058 | 1 | 19 | 0,29% |
| 8 | GP Combustíveis | 14,5 h | 1.188 | 2 | 23 | 0,25% |
| 9 | Midas Combustíveis | 10,5 h | 1.096 | 2 | 3 | 0,00% |
| 10 | Petronac | 4,5 h | 256 | 1 | 10 | 0,00% |
| 11 | Argemil Distribuidora | 3,5 h | 242 | 1 | 3 | 0,00% |
| 12 | BP | 2,5 h | 106 | 1 | 0 | 0,00% |
| | **Total clientes** | **905,0 h** | **97.682** | **24** | **385** | 0,72% |

# 2. Concentração & risco de dependência

Quão exposta está a receita a poucos clientes — e, dentro deles, a poucas pessoas.

- **~60% de tudo é uma só conta.** A Copercana sozinha responde por ~60% do tráfego e ~56% do tempo de uso. As outras 11 empresas somadas usam menos que ela.
- **61% num único usuário.** Dentro da Copercana, uma pessoa (`administrativodist@`) faz 61% das requisições. **Flexpetro, Small, Setta e Petronac operam com 1 usuário só.**

> 🟢 **Ação:** conversa de CS/comercial, não de engenharia — **ampliar a base de usuários** nas contas de usuário único. Férias ou desligamento derrubam o uso do cliente pela metade.

# 3. Saúde por cliente (taxa de erro)

Quem está com experiência degradada sem ninguém notar. Média da base: **0,72%**.

- 🔴 **Larco Petróleo — 5,89%, o pior da base.** 241 erros em 4.091 requisições, ~7× a média. Nenhuma outra empresa passa de 0,82%. O cliente sente e ninguém abriu chamado.
- Fora a Larco, a base está saudável: Rede Petro em 0,04%, Copercana em 0,70%. O problema é **pontual, não sistêmico**.

> 🔴 **Ação:** cruzar a Larco com o Sentry e **abrir ticket**. Erro concentrado em um cliente é sinal de churn silencioso.

# 4. Funil de trials

5 empresas passaram por trial em ~60 dias. **Nenhuma exercitou o produto** — o melhor caso usou 7 de 50 uploads.

| Empresa | Início | Expira | Uploads | Situação | Observação |
|---------|:------:|:------:|:-------:|----------|------------|
| Watt Distribuidora | 12/05 | 11/06 | 0 / 50 | expirado | AutoMind operou |
| PetroRio | 09/06 | 09/07 | 1 / 50 | expirado | AutoMind operou |
| Vopak | 11/06 | 11/07 | 7 / 50 | expirado | único c/ usuário real |
| **Petroserra** | 22/06 | **22/07** | 1 / 50 | **vence HOJE** | AutoMind operou |
| Tecab | 03/07 | 02/08 | 0 / 50 | ativo | AutoMind fez 2× o cliente |

> ⚠️ **Atenção:** em **3 dos 5 trials quem mais operou foi a AutoMind**, não o cliente. Os trials são criados **manualmente** (o fluxo self-service não está em uso) e o alerta interno de expiração não escala.

> 🟢 **Ação:** **Petroserra vence hoje (22/07)** — já escalada ao marketing em 20/07. **Tecab** (0 uploads, vence 02/08) segue sem tratativa.

# 5. Clientes inativos & custo sem receita

Onde há consumo de infraestrutura (OCR/Textract) sem cliente ativo por trás.

- 👻 **Atvos — suspensa, mas processando.** Marcada como suspensa no cadastro e mesmo assim **classificou 54 documentos em 30 dias**. Ou a suspensão não bloqueia o pipeline, ou a flag está errada — em ambos os casos, Textract pago de cliente que deveria estar parado.
- 👻 **Demonstração comercial — lote fantasma.** Sem nenhum cliente real, o worker rodou **666 OCR / 600 classify**: é o **mesmo lote de 111 documentos reprocessado 6×**. Custo de Textract recorrente sem receita.

> ⚠️ **Nota:** inativos reais (zero uso em ~59d): **Transportadora Providência**, **Assunção Distribuidora** (marcada ativa, nunca gerou 1 requisição) e **Ciapetro**. Um tenant totalmente parado não gera log — a lista completa só vem do banco/Portal de Assinantes.

# 6. Uso real: pessoas x máquina (polling)

De 122.248 requisições, só **12.860 (10,5%)** são ações deliberadas. O resto é o app "respirando" (`unread_count`, `permissions`, `trial/status`).

| Tipo de tráfego | Requisições | Fatia |
|-----------------|------------:|------:|
| Polling (máquina) | 109.388 | **89,5%** |
| Ação real (pessoa) | 12.860 | 10,5% |

Só o `unread_count` soma ~69 mil chamadas — a Copercana gera 39 mil dele sozinha. O produto é usado como **consulta** (listar/buscar documentos), não como esteira: foram apenas **385 uploads em 30 dias** entre todos os clientes.

> 🟢 **Ação:** trocar polling por **push/WebSocket** ou aumentar o intervalo — é o maior ganho de FinOps disponível hoje. Vale traduzir os 109 mil requests em R$ de infraestrutura.

# 7. Inventário de tenants de produção

Quantos clientes e tenants temos de fato — e por onde eles entram.

- **19 tenants com atividade** nos últimos 30 dias: 12 de cliente + 7 internos (AutoMind, suporte, demonstração, Portal de Assinantes).
- 🟠 **6 de 12 clientes só aparecem no processamento (worker).** Metade dos clientes **nunca toca a web** — entram por integração/API (Logum, Unibras, Watt, Vopak, PetroRio, entre outros). Qualquer análise só pela web os classifica errado como inativos.

> ⚠️ **Nota:** este é o **ponto cego** do produto — o volume de negócio pesado entra por integração, invisível no log web. Medir esses clientes de verdade depende de instrumentação no backend (Bloco B).

# Método & confiabilidade

Dados extraídos em **20/07/2026** do Grafana/Loki (jobs `autochecker-backend` / `celery-tasks`, ambiente de produção) e Sentry (org `automind-qd`), janela de 30 dias.

- **Sei:** requisições, usuários, rotas, uploads, erros, tenants.
- **Parcial:** tempo de uso (proxy de janelas de 30 min — superestima quem deixa a aba aberta).
- **Não sei (depende de dev):** tipo de documento, tempo de sessão real, uso via integração/API por cliente.

**Trials:** uploads e dias são "último observado" (o endpoint só responde quando alguém abre o app), não valor ao vivo; só a data de expiração é fixa.

**Não inclui** os indicadores que dependem de nova instrumentação — adoção por tela, usuários ativos reais, tipo de documento, tendência mês a mês e SLA (Bloco B, a combinar com o time de desenvolvimento).
