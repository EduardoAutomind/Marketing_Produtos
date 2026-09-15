# Análise do ambiente `prd` — AutoLoad V4

> Views, funções e páginas mais utilizadas em produção, com performance, erros, base de usuários e contexto de infraestrutura.

| | |
|---|---|
| **Data** | 17/06/2026 |
| **Produto** | AutoLoad V4 (backend .NET 8 · frontend Next.js 14 · EdgeGateway .NET 8 Worker · portal-cliente) |
| **Org Sentry** | `automind-qd` |
| **Ambiente** | `prd` (produção) |
| **Janela** | Últimos 30 dias |
| **Fonte** | Dados ao vivo do Sentry (dataset `spans` e `errors`) cruzados com o código em `Produtos/Autoload V4/` |

---

## ⚠️ Premissa: só o frontend tem telemetria em produção

Dos 4 projetos Sentry do AutoLoad V4, **apenas `autoloadv4-frontend` envia dados no ambiente `prd`**. O backend, o portal-cliente e o edgegateway **não enviam nada em produção** (detalhe e causa raiz na investigação separada `Investigacao_Sentry_Producao_AutoLoad_2026-06-17.md`).

**Consequência metodológica:** as "funções/views" de backend abaixo foram reconstruídas **indiretamente**, a partir das chamadas HTTP que o frontend registra (spans `http.client`). É uma visão fiel do que a API atende em produção, mas sem latência/erro server-side — esses só existirão quando o `SENTRY_DSN` for injetado na release do backend.

---

## 📊 1. Retrato do ambiente `prd`

| Métrica | Valor |
|---|---|
| Transações (30d) | **84.800** |
| Usuários únicos | **404** |
| Domínio de produção | `autoload.cloud` |
| Infraestrutura | Atrás de **Cloudflare** (beacon `POST /cdn-cgi/rum`) |
| Tempo real | **SignalR** — hubs `messages` e `telemetry` (`/hubs/.../negotiate`) |
| Bootstrap de config | `GET /env.json`, `GET /version.json` no carregamento |

É uma operação real com ~400 usuários — não um piloto. O "cliente" que opera essas telas é o **operador/admin** da unidade (não um motorista/portal externo).

---

## 🖥️ 2. Telas mais usadas — navegação real do usuário

Visão mais fiel do uso: transações `op:navigation` = clique → tela renderizada, com a latência que o usuário **de fato sente** (client-side).

| # | Tela | Navegações | p75 | p95 |
|---|------|----------:|----:|----:|
| 1 | **Programações** (lista) | 1.520 | 1,53 s | 🔴 5,22 s |
| 2 | **Programação – detalhe** `/programs/:modal/:id` | 1.420 | 1,07 s | 2,79 s |
| 3 | **Programação – operação** `.../operation/:operationId` | 660 | 0,87 s | 3,25 s |
| 4 | **Home Admin** `/admin` | 640 | 0,31 s | 2,33 s |
| 5 | **Dashboard** | 570 | 1,14 s | 3,67 s |
| 6 | **Estoque – Movimentações** | 400 | 1,18 s | 2,26 s |
| 7 | **Estoque – Cortes (cutoffs)** | 330 | 0,52 s | 🔴 4,20 s |
| 8 | **Login** | 290 | 0,73 s | 1,13 s |
| 9 | **Gateway** | 250 | 1,04 s | 2,92 s |
| 10 | **Corte – detalhe** `/cutoffs/:id` | 210 | 🔴 2,20 s | 3,78 s |
| 11 | **Estoque – Volumes** | 140 | 1,20 s | 3,31 s |

**Leitura:** o módulo **Programações concentra ~50% da navegação** (lista + detalhe + operação ≈ 3.600) e é também o mais pesado — a lista tem **p95 de 5,2 s**, a pior experiência das telas de alto tráfego.

### Nota técnica: os 3 "formatos" da mesma rota no Sentry

| Formato | O que é | Latência típica |
|---|---|---|
| `GET /pt-BR/admin/...` | Route handler server-side (rota localizada) | 2 ms |
| `GET /[locale]/admin/...` | Route handler server-side (rota paramétrica) | ~80 ms |
| `/:locale/admin/...` (`op:navigation`/`pageload`) | **Client-side real (UX)** | 1–2 s |

Para "o que o usuário sente", a referência é o terceiro formato.

---

## 🧭 3. Telas mais usadas — contagem por rota (server-side)

Visão de volume bruto de requisições por rota (todos os formatos), consolidando variantes da mesma tela:

| # | Página | Acessos (prd) |
|---|--------|--------------:|
| 1 | **Programações** (lista + detalhe + roadway) | ~15.600 |
| 2 | Dashboard | ~4.390 |
| 3 | Landing / Login (`/` + `/[locale]`) | ~4.010 |
| 4 | Estoque – Movimentações | ~3.240 |
| 5 | Configurações | ~3.010 |
| 6 | Home Admin | ~2.560 |
| 7 | Gateway | ~2.480 |
| 8 | Agendamentos | ~2.090 |
| 9 | Dispositivos | ~2.010 |
| 10 | Área Operacional | ~1.830 |
| 11 | IA | ~1.760 |
| 12 | Checklists | ~1.090+ |
| 13 | Auditoria | ~920 |
| 14 | Presets | ~890 |
| 15 | Circuitos | ~840 |

---

## 🔌 4. Funções / views de backend exercitadas em `prd`

Reconstruído a partir das chamadas `http.client` do frontend (domínio `autoload.cloud/api`):

| # | Função / endpoint | Chamadas | O que é |
|---|---|----------:|---|
| 1 | `GET /api/v1/programs` | 6.120 | Alimenta a tela #1 (Programações) |
| 2 | `GET /api/v1/messages` | 5.960 | Mensageria / notificações |
| 3 | `POST /hubs/messages/negotiate` | 5.630 | Handshake SignalR (tempo real) |
| 4 | `GET /api/v1/users/{id}/preferences` | 5.540 + 4.130 + … | Preferências por usuário (em quase toda tela) |
| 5 | `GET /api/v1/organizations` | 4.070 | Contexto multi-tenant |
| 6 | `POST /api/v1/users/{id}/preferences` | 2.310 + 1.880 | **Escrita** frequente de preferências |
| 7 | `POST /hubs/telemetry/negotiate` | 2.290 | Hub de telemetria em tempo real |
| 8 | `GET /api/v1/products` | 1.190 | Cadastro de produtos |
| 9 | `GET /api/v1/storagetanks` | 1.090 | Tanques de armazenamento |
| 10 | `GET /api/v1/attachments` | 920 | Anexos / evidências |
| — | `GET /api/v1/auth/current_user` | 740 | Sessão |
| — | `GET /api/v1/parameters/{terms_of_use_url, tags, units}` | ~2.000 | Parâmetros de bootstrap |
| — | `GET /env.json`, `GET /version.json` | ~1.450 | Config / versão no load |

**Insight:** `preferences` (GET + POST) somadas passam de **14k chamadas** — é o endpoint mais "quente" da API em produção, acima até de `programs`. Sugere leitura/escrita repetida de preferências por tela (candidato a cache / debounce).

---

## 🐛 5. Erros reais em produção (`prd`)

| Erro | Eventos | Usuários | Avaliação |
|---|----:|----:|---|
| `Object.s` | 322 | 7 | 🔴 Top erro, mas **minificado** — faltam source maps |
| `TypeError: Failed to fetch (autoload.cloud)` | 133 | 14 | Falha de rede/API — **maior dispersão de usuários** |
| `<unknown>` | 32 | 15 | Sem stack útil |
| `Cannot read properties of null (reading 'digest')` | 30 | 13 | Tratamento de erro do Next.js |
| `Unable to load shared library 'libwkhtmltox'` | 9 | 3 | 🔴 **Geração de PDF quebrada** em prod (wkhtmltopdf) |
| `AggregateError: No error message` | 8 | 1 | Sem mensagem |
| `Server returned handshake error: Handshake was canceled` | 5 | 2 | Reconexão SignalR (ruído) |
| `DateTime '...?tags=terminal:...' não reconhecido` | 1 | 1 | Query param malformado p/ backend |
| `Object Not Found Matching Id… MethodName:update` | 2 | 2 | Ruído típico de WebSocket/SignalR |

**Destaques:**

- **Source maps ausentes** — o erro nº1 (`Object.s`) é nome minificado, inútil para debug. Subir source maps no build do frontend é quick win e encaixa direto no roadmap de observabilidade.
- **`libwkhtmltox`** — feature real (exportação/relatório em PDF) **quebrada em produção** por dependência nativa faltando no container. Atinge poucos usuários só porque poucos usam PDF, mas a feature está 100% inoperante.
- **`Failed to fetch`** (14 usuários) — maior dispersão; investigar correlação com as telas lentas (Programações p95 5 s pode estar estourando timeout de requisição).

---

## 💡 6. Síntese e recomendações (alinhadas ao cronograma)

1. **Programações é o coração e o gargalo.** Tela mais usada (~50% da navegação) e a mais lenta (p95 5,2 s). Otimizar aqui tem o maior retorno de UX. Provável causa: `GET /api/v1/programs` (6,1k chamadas) sem paginação/cache eficiente.
2. **Preferências de usuário super-chamadas** (14k+). Investigar leitura/escrita repetida por tela → cachear / consolidar.
3. **Subir source maps** do frontend — sem isso o erro nº1 de produção é cego.
4. **Corrigir `libwkhtmltox`** no container de produção (feature de PDF morta).
5. **Backend sem telemetria** (item já levantado). Hoje a análise de API é indireta. Com `SENTRY_DSN` na release do backend, veremos latência/erro server-side de cada endpoint diretamente.
6. **Higiene de ambiente:** segue o `production` órfão (1,5k eventos) convivendo com `prd`; backend tem `dev` E `Development`. Padronizar para um valor único por ambiente.

---

## Anexo — Notas de método

- Todas as contagens são do dataset `spans` (transações e spans `http.client`) e `errors`, filtradas por `environment:prd`, janela 30 dias, projeto `autoloadv4-frontend`.
- Latências `p75`/`p95` em `span.duration` (ms convertidos para s nas tabelas).
- "Usuários únicos" = `count_unique(user)` no período.
- Consulta feita **projeto a projeto** (agregados org-wide do MCP vêm truncados).

*Documento gerado em 17/06/2026 a partir de dados ao vivo do Sentry.*
