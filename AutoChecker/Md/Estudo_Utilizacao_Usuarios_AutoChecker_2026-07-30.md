# Estudo de Utilização de Usuários — AutoChecker

Levantamento **ao vivo** dos logs de produção no Grafana/Loki, janela de **30 dias corridos até 30/07/2026**. Encomendado pela gestão para responder: **como está a utilização dos usuários no AutoChecker?**

> ⚠️ **Confidencial · uso interno AutoMind.** Contém nome, e-mail e comportamento de usuários identificados de clientes reais. Não distribuir fora da gestão.

---

## Resumo executivo

**O AutoChecker é usado por cerca de 30 pessoas de cliente por mês, e quase metade de toda a atividade de login é da própria AutoMind.** Das 336 entradas no produto na janela, **152 (45%) são contas internas** — a conta `superadmin@autochecker.cloud`, sozinha, entrou **92 vezes, mais que qualquer cliente** (o cliente mais ativo entrou 25 vezes). Do lado do cliente, o trabalho real é pequeno em volume mas concentrado: **531 envios de documento em 30 dias**, ou seja **~18 por dia**, sendo que **uma única pessoa responde por 15% de todos os envios**. E **8 das 14 empresas clientes dependem de uma única pessoa** — se ela sai de férias, a conta apaga.

Três achados fora do escopo original mudam decisões já tomadas:

1. **O contador de uploads do trial está quebrado.** A Tecab **enviou 9 documentos com sucesso** em 10 e 13/07, e o painel de trial continuava marcando `0 de 50` em 22/07. A conclusão anterior — registrada no inventário de 27/07 e usada comercialmente — de que *"nenhum trial usou o produto"* **está errada**.
2. **O login é sensível a maiúsculas** (confirmado no código). Um usuário perdeu **11 tentativas** digitando o e-mail em caixa alta.
3. **6 pessoas nunca conseguiram entrar** na janela — incluindo alguém de um cliente ativo e alguém de uma empresa que não aparece em nenhum outro lugar.

**93% do tráfego é a máquina falando com ela mesma** (polling), não pessoas trabalhando. Qualquer leitura de "uso" baseada em volume de requisição — inclusive os estudos anteriores deste projeto — superestima a atividade humana por duas ordens de grandeza.

---

## Ressalva de método — leia antes dos números

**Login mede entrada, não uso.** O token de sessão (`refresh`) vale **30 dias**, então quem entra uma vez pode trabalhar o mês inteiro sem novo login. Isso é decisivo: `faturamentoribeiraopreto@flexpetro.com` aparece com **1 único login** e fez **59 envios de documento**. Ler "1 login" como "não usou" seria errado.

Por isso este estudo usa **duas métricas separadas**:

| Métrica | O que mede | Boa para |
|---|---|---|
| **Logins** (`/api/accounts/login/step2/` 200) | quantas vezes a pessoa **entrou** | assento vivo, retomada, atrito de acesso |
| **Envios** (`/api/documents/upload/multi/`) | quantas vezes a pessoa **trabalhou** | utilização real, dependência, valor entregue |

Outras ressalvas:

- **Existe um segundo caminho de login** (`/api/accounts/firebase/login/step1/`, Google) com 5 entradas em 30d, e um caminho de **auto-cadastro de não-assinante** (`register-non-subscriber`, 5 cadastros). Somados, ~1,5% de subcontagem nos logins — pequeno, mas os não-assinantes **não aparecem no funil de login** e ainda assim trabalham.
- **Total de logins: 336 pela matriz diária, 319 em leitura de janela única.** Diferença é efeito de borda do primeiro bucket. Não muda conclusão; onde o número importa, uso 336.
- **Teto da janela:** o log com `user_email` só começa por volta de **15/06/2026**. Não há como fazer coorte ou tendência de mais de ~6 semanas.
- **4 contas `@basecompartilhada.com.br`** (24 logins, 35 envios) ficaram **fora** da contagem de cliente — não sei se são cliente ou operação AutoMind. **Precisa sua confirmação**; se forem cliente, os totais de cliente sobem ~13%.

---

## 1. Utilização de assentos — quem entra

**41 contas** entraram no produto em 30 dias: **26 de cliente**, 11 internas AutoMind, 4 indefinidas.

| Classe | Contas | Logins | % dos logins |
|---|--:|--:|--:|
| Cliente | 26 | 160 | 48% |
| **Interno AutoMind / superadmin** | **11** | **152** | **45%** |
| Indefinido (`@basecompartilhada`) | 4 | 24 | 7% |

A conta `superadmin@autochecker.cloud` fez **92 logins** — mais que qualquer cliente e 58% de todo o acesso interno. Vale checar se é uso legítimo de suporte ou automação rodando com credencial de superadmin.

### Contas de cliente, por login

| Conta | Empresa | Logins | Dias ativos | Último acesso | Silêncio |
|---|---|--:|--:|---|--:|
| faturamento1@biopetro.com.br | Biopetro | 25 | 12 | 28/07 | 2d |
| controladoriadist2@copercana.com.br | Copercana | 22 | 13 | 30/07 | 0d |
| rvandre@redepetro.com.br | RedePetro | 21 | 11 | 22/07 | **8d** |
| administrativodist@copercana.com.br | Copercana | 14 | 12 | 30/07 | 0d |
| marcia.galatte@settacombustiveis.com.br | Setta | 11 | 7 | 30/07 | 0d |
| faturamento@redepetro.com.br | RedePetro | 10 | 6 | 28/07 | 2d |
| flaviaminhuk@redepetro.com.br | RedePetro | 9 | 9 | 29/07 | 1d |
| reism@midascombustiveis.com | Midas | 9 | 4 | 29/07 | 1d |
| faturamentobio@biopetro.com.br | Biopetro | 8 | 3 | 28/07 | 2d |
| faturamentodist@copercana.com.br | Copercana | 7 | 5 | 29/07 | 1d |
| faturamentodist2@copercana.com.br | Copercana | 3 | 2 | 20/07 | 10d |
| faturamentodist3@copercana.com.br | Copercana | 3 | 2 | 04/07 | **26d** |
| mariane.santi@argemildistribuidora.com.br | Argemil | 3 | 3 | 27/07 | 3d |
| cadastro@tecab.srv.br | **Tecab (trial)** | 2 | 1 | 09/07 | **21d** |
| leonardo.aparecido@small.com.br | Small | 2 | 1 | 27/07 | 3d |
| *(+10 contas com 1 login)* | | 1 cada | 1 | — | 2 a 30d |

### Distribuição de engajamento (contas de cliente)

| Dias com acesso no mês | Contas |
|---|--:|
| 1 dia só | 13 |
| 2 a 3 dias | 4 |
| 4 a 7 dias | 4 |
| 8 a 14 dias | 5 |
| **15 dias ou mais** | **0** |

**Nenhuma conta de cliente entrou em 15 dias ou mais do mês.** O uso mais intenso do produto é de meio período: 13 dias em 30, no melhor caso. Isso é coerente com fluxo de faturamento (concentra em fechamento), não com uso diário de operação.

### 🔴 Sinal de atenção — engajado que silenciou

`rvandre@redepetro.com.br` é o **3º cliente mais ativo** (21 logins, 11 dias) e está **8 dias sem entrar**. Perda de um usuário forte é sinal de churn muito mais confiável que a saída de quem já usava pouco. Vale um contato de CS.

---

## 2. Funil de tarefa real — quem entra realmente trabalha?

Volumes de 30 dias, produto inteiro:

| Passo | Caminho | Requisições |
|---|---|--:|
| Entrar | `login/step2/` (200) | **319** |
| Carregar permissões | `core/permissions/` | 21.454 |
| Abrir lista de documentos | `documents/` | 3.497 |
| **Enviar documento** | **`documents/upload/multi/`** | **531** |
| Ver processados | `documents/processed/` | 406 |

**A boa notícia:** 319 logins geram 531 envios — **1,7 envio por entrada**. Quem entra, na média, trabalha. Não é um produto que as pessoas abrem e abandonam.

**A má notícia:** são **21.454 chamadas de permissão para 531 envios — 40 chamadas de permissão por documento enviado.** É o endpoint mais chamado depois do polling de notificação, e é exatamente o que travava 120s no incidente do Redis reportado em 28/07. Cada envio de documento custa 40 idas ao endpoint mais frágil do sistema.

### 🔴 6,6% dos envios falham com erro de servidor

| Resposta do envio | Ocorrências |
|---|--:|
| 207 (sucesso / multi-status) | 496 |
| **500 (erro de servidor)** | **35** |

**35 envios em 30 dias morreram com erro 500.** É a ação central do produto — a pessoa selecionou o documento, esperou e recebeu erro. Não aparece como incidente nos relatórios semanais porque o volume absoluto é baixo, mas em cima de 531 tentativas é **1 em cada 15**.

---

## 3. Dependência de pessoa-chave

### Por empresa (clientes)

| Empresa | Contas | Logins | Concentração na 1ª pessoa | Último acesso |
|---|--:|--:|--:|---|
| Copercana | 6 | 50 | 44% | 30/07 |
| RedePetro | 4 | 41 | 51% | 30/07 |
| Biopetro | 2 | 33 | **76%** | 28/07 |
| Setta | 1 | 11 | **100%** | 30/07 |
| Midas | 1 | 9 | **100%** | 29/07 |
| Argemil | 1 | 3 | **100%** | 27/07 |
| Small | 2 | 3 | 67% | 27/07 |
| Larco | 2 | 2 | 50% | 29/07 |
| GP Combustíveis | 2 | 2 | 50% | 21/07 |
| Tecab (trial) | 1 | 2 | **100%** | 09/07 |
| Grupo CPA | 1 | 1 | **100%** | 07/07 |
| Flexpetro | 1 | 1 | **100%** | 16/07 |
| Vitreum | 1 | 1 | **100%** | 29/07 |
| Guterres | 1 | 1 | **100%** | 10/07 |

**8 das 14 empresas clientes têm uma única pessoa usando o produto.** Nessas contas não existe redundância: férias, desligamento ou troca de função apagam o cliente do produto. Copercana e RedePetro são as únicas com base de usuários realmente distribuída.

### Concentração de trabalho (envios de documento)

| Pessoa | Empresa | Envios | % do total |
|---|---|--:|--:|
| controladoriadist2@copercana.com.br | Copercana | 80 | **15,1%** |
| faturamentoribeiraopreto@flexpetro.com | Flexpetro | 59 | 11,1% |
| janaina.cristina@small.com.br | Small | 46 | 8,7% |
| marcia.galatte@settacombustiveis.com.br | Setta | 41 | 7,7% |
| faturamentodist4@copercana.com.br | Copercana | 31 | 5,8% |
| flaviaminhuk@redepetro.com.br | RedePetro | 25 | 4,7% |
| rvandre@redepetro.com.br | RedePetro | 25 | 4,7% |
| administrativodist@copercana.com.br | Copercana | 20 | 3,8% |
| jpedro@petronac.com.br | Petronac | 20 | 3,8% |
| faturamento1@biopetro.com.br | Biopetro | 16 | 3,0% |

**Aqui o ranking muda de forma importante em relação aos estudos anteriores.** Três pessoas no topo de envios têm **1 único login** no mês (Flexpetro, Small, e `faturamentodist4@copercana`) — trabalharam o mês inteiro numa sessão só. E `jpedro@petronac.com.br` fez 20 envios **sem nenhum login** registrado: entrou pelo caminho de não-assinante. Nenhum dos três apareceria num ranking por login.

---

## 4. Atrito na porta de entrada

**32 combinações de e-mail × erro** de login em 30 dias. Três padrões, um deles confirmado como bug de produto.

### 🔴 Login é sensível a maiúsculas — CONFIRMADO no código

| Variação tentada | Resultado |
|---|--:|
| `RENATO@BASECOMPARTILHADA.COM.BR` | **11 × 401** |
| `renato@basecompartilhada.com.br` | 16 logins OK |
| `RVANDRE@redepetro.com.br` | **2 × 401** |
| `rvandre@redepetro.com.br` | 21 logins OK |

**Causa confirmada no código-fonte:** `backend/apps/accounts/views.py:3384` e `views.py:3429` fazem `User.objects.get(email=email, is_active=True)` — comparação **exata**, sem `__iexact` nem normalização por `.lower()`. No PostgreSQL isso é case-sensitive. Quem digita o e-mail em caixa alta (celular com autocapitalização, por exemplo) **não entra e recebe "credenciais inválidas"** — mensagem que joga a culpa na senha.

**Correção:** normalizar o e-mail na entrada (`email.strip().lower()`) ou trocar por `email__iexact`. Duas linhas, e resolve 13 falhas de login rastreadas em um mês.

### 🟠 Domínio errado — `@automind.co` em vez de `@automind.com.br`

11 falhas de 4 pessoas da própria AutoMind (`daniel.almeida`, `eduardo.santos`, `tarcisio.rocha`, `victor.nascimento`). Curiosamente há **1 login bem-sucedido** com `paulo.sacramento@automind.co`, o que sugere que existe conta cadastrada no domínio errado. Vale conferir o cadastro.

### 🔴 6 pessoas que nunca conseguiram entrar

Aparecem apenas como falha, nunca como login bem-sucedido, em toda a janela:

| E-mail | Erro | Observação |
|---|---|---|
| `logistica@redepetro.com.br` | 2 × 401 | **Cliente ativo** — colega dos 4 usuários que entram normalmente |
| `claudia.takano@terin.com.br` | 2 × 401 | Empresa não aparece em nenhum outro lugar do produto |
| `rafael.araujo@girologistica.com.br` | 1 × 401 | Idem |
| `logistica@bassultransportes.com.br` | 1 × 401 | Idem |
| `valdir@ruff.com.br` | 1 × 401 | Idem |
| `amandadssouza@gmail.com` | 1 × 401 | Conta pessoal |

As 4 empresas do meio da tabela (Terin, Giro Logística, Bassul, Ruff) **não existem em nenhum tenant ativo**. São prospects tentando entrar, ou usuários que perderam acesso. Em ambos os casos é receita ou retenção parada na porta — e ninguém está olhando, porque falha de login não gera alerta.

O 403 é caso diferente: vem de `is_suspended` (`views.py:3386`), ou seja usuário suspenso tentando entrar. Ocorreu com `fabioestacio@grupocpa.com.br`, `flaviaminhuk@redepetro.com.br`, `leonardo.aparecido@small.com.br` e `jpedro@petronac.com.br`.

### 🟠 Contas de teste em produção

`joao@gmail.com` (2 envios), `vitoria@gmail.com` (4 falhas), `rvandre@gmail.com`, `joaomotorista@gmail.com`. Poluem qualquer métrica de usuário e, no caso de `joao@gmail.com`, **enviaram documento de verdade** em produção.

---

## 5. Máquina × humano — o que o volume realmente é

Top 28 caminhos, 30 dias: **140.539 requisições**.

| Caminho | Requisições | % |
|---|--:|--:|
| `notifications/inbox/unread_count/` | **81.782** | **58,2%** |
| `core/permissions/` | 21.454 | 15,3% |
| `trial/status/` | 6.621 | 4,7% |
| `notifications/inbox/` | 5.793 | 4,1% |
| `tenants/all-tenants-switcher/` | 5.718 | 4,1% |
| `documents/upload-usage/` | 4.719 | 3,4% |
| `documents/` | 3.497 | 2,5% |
| `accounts/me/` | 1.981 | 1,4% |
| `legal/acceptances/status/` | 1.674 | 1,2% |
| `token/refresh/` | 1.096 | 0,8% |
| **`documents/upload/multi/`** | **531** | **0,4%** |
| `documents/processed/` | 406 | 0,3% |
| Sondagem de robô (`.env`, `graphql`, `config`, `settings`) | ~2.235 | 1,6% |

**Polling e manutenção de tela somam ~130.800 requisições — 93% do tráfego.** A ação que entrega valor ao cliente é **0,4%**.

Consequências práticas:

- **Um único endpoint de contagem de notificação não lida é 58% de todo o tráfego do produto.** Se o intervalo de polling dele for ampliado (por exemplo de 5s para 30s), o tráfego do AutoChecker cai pela metade — junto com custo de log, custo de banco e carga no Redis que já causou o incidente de 120s.
- **`trial/status/` é chamado 6.621 vezes em 30 dias** para 1 tenant em trial. Está sendo consultado em loop mesmo por quem não é trial.
- Todo estudo anterior deste projeto que ranqueou cliente por **volume de requisição ou tempo de sessão** estava medindo, em 93%, o navegador conversando com o servidor. Os rankings mudam quando a métrica passa a ser envio de documento — como mostra a seção 3.

---

## 6. 🔴 Achado crítico — contador de uploads do trial está quebrado

Este achado apareceu por acaso, ao cruzar o funil com o inventário de trials de 27/07. Ele **invalida uma conclusão comercial já registrada**.

**O que o inventário de 27/07 e o estudo de funil de trials afirmaram:** a Tecab estava em trial com `0 de 50` uploads usados, a 9 dias de vencer — *"trial que não engatou"*, e mais amplamente *"nenhum dos 5 trials usou o produto"*.

**O que os logs mostram:**

| Evidência | Valor |
|---|---|
| Login da Tecab | 09/07/2026 (1 dia, 2 logins) |
| Envios de documento | **9 requisições**, em 10/07 (7) e 13/07 (2) |
| Resposta HTTP de todos os 9 | **207** — nenhum 500, nenhum 4xx |
| Corpo da resposta (amostra de 13/07 09:36) | `"total_files": "1", "success_count": "1", "status": "success"` |
| `/api/trial/status/` lido em 22/07 | `"uploads_used": "0", "uploads_limit": "50"` |

**A Tecab enviou 9 documentos com sucesso confirmado e o contador do trial marcava zero 9 dias depois.** Não é interpretação: a própria resposta da API de upload diz `success_count: 1` e `status: success`, e a API de trial diz `uploads_used: 0`.

**Impacto:**

- **Comercial.** A leitura de que o trial não engatou é falsa. A Tecab experimentou o produto e parou — o que é um problema **diferente** e exige conversa diferente. O trial vence **02/08/2026**, ou seja **em 3 dias**.
- **Metodológico.** Todo o funil de trials deste projeto foi construído sobre `uploads_used`. Se o campo não incrementa, os 5 trials analisados precisam ser relidos por envio real, não pelo contador.
- **Produto.** Se o limite de 50 uploads é regra de negócio do trial, ele **não está sendo aplicado** — um trial pode enviar sem limite.

**Detalhe adicional:** as leituras de `/api/trial/status/` da Tecab que eu inspecionei foram feitas por `superadmin@autochecker.cloud` a partir do IP `174.138.38.7` — ou seja, **quem estava olhando o trial era a AutoMind**, não o cliente.

---

## 7. O que sabemos, o que é hipótese, o que não dá para medir

**✅ Medido e confirmado**

- 41 contas com login em 30d; divisão 26 cliente / 11 interno / 4 indefinido; 336 logins.
- `superadmin@autochecker.cloud` com 92 logins, acima de qualquer cliente.
- 531 envios de documento, 35 deles com HTTP 500 (6,6%).
- Distribuição de engajamento: 13 contas de cliente com 1 único dia de acesso; **nenhuma** com 15+ dias.
- Concentração por empresa e por pessoa (seção 3), incluindo as 8 empresas com usuário único.
- **Case-sensitivity do login** — confirmado em duas fontes independentes: padrão nos logs (13 falhas em caixa alta contra sucessos em minúscula, mesmas pessoas) **e** o código em `views.py:3384` / `views.py:3429`.
- **Contador do trial quebrado** — confirmado pela resposta da própria API de upload (`success_count: 1`) contra a resposta da API de trial (`uploads_used: 0`).
- 93% do tráfego é polling; `unread_count` sozinho é 58,2%.

**🟡 Indício, não fato**

- **Motivo das 6 pessoas que não entraram.** Sei que falharam com 401 e nunca entraram. **Não sei** se é senha esquecida, conta nunca criada ou prospect curioso — o log não distingui "usuário não existe" de "senha errada" (a mensagem é a mesma para os dois casos, o que por si só é uma escolha discutível de UX).
- **`superadmin` com 92 logins.** Parece uso de suporte/automação, mas **não verifiquei** se é pessoa ou script.
- **Silêncio de `rvandre@redepetro` como churn.** 8 dias sem entrar num usuário forte é sinal, não conclusão — pode ser férias.
- **As 4 contas `@basecompartilhada.com.br`.** Não classifiquei. Se forem cliente, os números de cliente sobem ~13%.

**❓ Não dá para medir hoje**

- **Tipo de documento enviado.** Não é logado. Não há como dizer *que* documento os clientes mais validam — pergunta que a gestão vai fazer.
- **Tempo real de sessão.** Não há evento de início/fim de sessão nem logout. Qualquer "tempo no produto" é estimativa por intervalo entre requisições, e com token de 30 dias a estimativa piora.
- **Desfecho do documento enviado.** Sei que 531 envios entraram; **não sei** quantos terminaram validados, porque o desfecho fica no worker e não é correlacionado ao usuário que enviou.
- **Janela maior que ~6 semanas.** O log com `user_email` começa por volta de 15/06/2026. Coorte, retenção mês-a-mês e sazonalidade estão fora de alcance até acumular histórico.
- **Quantas licenças foram vendidas.** Este estudo mede quem **usou**, não quem **tem direito**. A comparação assento-vendido × assento-usado — a pergunta comercial mais direta — exige a base de contratos, que não está no log.

---

## 8. Ações sugeridas, por custo

| # | Ação | Depende de | Custo |
|--:|---|---|---|
| 1 | **Falar com a Tecab antes de 02/08** — o trial usou o produto, não ignorou | Comercial/CS | Horas |
| 2 | **Corrigir o contador de uploads do trial** e reler os 5 trials por envio real | Dev | Baixo |
| 3 | **Normalizar e-mail no login** (`.lower()` ou `__iexact`) — 2 linhas | Dev | Trivial |
| 4 | **Contatar as 6 pessoas que não entraram**, começando por `logistica@redepetro.com.br` (cliente ativo) | Suporte | Horas |
| 5 | **Contato de CS com `rvandre@redepetro.com.br`** — usuário forte, 8 dias em silêncio | CS | Horas |
| 6 | **Ampliar o intervalo de polling do `unread_count`** — corta ~metade do tráfego e alivia o Redis | Dev | Baixo |
| 7 | **Investigar os 35 erros 500 no envio** — 1 em cada 15 tentativas | Dev | Médio |
| 8 | **Remover contas de teste de produção** (`joao@gmail.com` e afins) | Dev/Suporte | Baixo |
| 9 | **Auditar os 92 logins do `superadmin`** — pessoa ou script? | Você | Horas |
| 10 | **Instrumentar tipo de documento e sessão** — destrava as duas perguntas que hoje não têm resposta | Dev | Médio |
| 11 | **Cruzar com a base de contratos** para fechar assento-vendido × assento-usado | Comercial | Médio |

---

### Notas técnicas

- **Fonte:** `{app="backend", environment="prod"}` no Loki de `monitor.autochecker.cloud`, arquivo `/var/log/autochecker/api.log`. Linha no formato `INFO {json}`.
- **Parsing:** extração por `| regexp` sobre o JSON, **nunca** `| json` — a linha é `INFO {json}` e o `response_body` vem duplamente escapado; `| json` sobre 30 dias também estoura o timeout de 90s.
- **Login concluído** = `POST /api/accounts/login/step2/` com `status_code: 200`. O `step1` apenas valida credencial e não representa entrada no produto.
- **Contagens** são de linhas de log (requisições), não de documentos. Um envio `upload/multi` pode conter mais de um arquivo.
- **Datas** dos buckets diários foram deslocadas em -1 dia: `count_over_time([1d])` rotula o bucket pelo **fim** da janela.
- **Código consultado:** `Produtos/Autochecker/AutoChecker/backend/apps/accounts/views.py`, função `login_step1` (linhas 3363 em diante).
