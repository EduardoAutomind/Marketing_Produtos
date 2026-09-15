# Investigação — Telemetria do AutoLoad V4 no Sentry (produção)

**Data:** 2026-06-17
**Org Sentry:** `automind-qd` · **Janela:** últimos 30 dias
**Produto:** AutoLoad V4 · **Fonte:** dados ao vivo do Sentry cruzados com o código em `Produtos/Autoload V4/`

---

## Pergunta que originou a investigação

1. Quais views/telas do AutoLoad os clientes mais usam?
2. Idem, **só em produção**.
3. Por que o **backend não envia dados de produção**?

---

## 1. Telas mais usadas (todos os ambientes)

Componente com uso real é o **Frontend Admin** (`autoloadv4-frontend`). Variantes de rota
(`/pt-BR/...`, `/[locale]/...`, `/:locale/...`) são a mesma tela e foram somadas.

| # | Tela | Rota | Acessos (30d) |
|---|------|------|--------------:|
| 1 | Programações | `/admin/programs` | ~20.200 |
| 2 | Configurações | `/admin/settings` | ~17.800 |
| 3 | Dashboard | `/admin/dashboard` | ~16.200 |
| 4 | Agendamentos | `/admin/appointments` | ~14.800 |
| 5 | Home Admin | `/admin` | ~14.400 |
| 6 | Estoque / Movimentações | `/admin/inventory/movements` | ~13.400 |
| 7 | Gateway | `/admin/gateway` | ~13.200 |
| 8 | Dispositivos | `/admin/devices` | ~12.100 |
| 9 | Checklists | `/admin/checklists` | ~11.700 |
| 10 | Área Operacional | `/admin/operational-area` | ~11.400 |

> `NextNodeServer.clientComponentLoading` (15.460) foi ignorado — é transação interna do Next.js, não uma tela.

---

## 2. Páginas mais acessadas em PRODUÇÃO (`environment:prd`)

O ambiente de produção está rotulado **`prd`** (não `production` — há um `production` órfão com 1.523 eventos).

| # | Página | Acessos (prd) |
|---|--------|--------------:|
| 1 | **Programações** (lista + detalhe + roadway) | **~15.600** |
| | ↳ lista `/admin/programs` | 8.063 |
| | ↳ detalhe `/admin/programs/[modal]/[id]` | 4.685 |
| | ↳ `/admin/programs/roadway/*` | 2.900 |
| 2 | Dashboard `/admin/dashboard` | ~4.390 |
| 3 | Landing / Login `/` + `/[locale]` | ~4.010 |
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

**Leitura:** em produção, **Programações domina muito mais** (~18% de todo o tráfego de páginas, mais que o dobro da 2ª). `Settings` cai de 2º p/ 5º — era inflado por homologação/dev. Aparecem fluxos de cliente real que somem no ruído: roadway, presets, circuits.

---

## 3. Por que o BACKEND não envia produção — causa raiz

### Distribuição por ambiente (backend, 30d)

| Ambiente | Erros | Transações |
|----------|------:|-----------:|
| `hml` | 1.226 | 154 |
| `dev` / `Development` | 210 + 204 | 56.726 |
| **`prd` / `production`** | **0** | **0** |

Em produção **não chega nada** — nem erro, nem transação.

### Mecanismo no código

`AUTOLOAD_V4_Backend/AutoloadV4.Api/Program.cs:53-70`:

```csharp
var sentryEnabled = (builder.Configuration.GetSection("Sentry:Dsn").Value ?? "#{SENTRY_DSN}#") != "#{SENTRY_DSN}#";
if (sentryEnabled)
{
    builder.WebHost.UseSentry(options =>
    {
        options.Dsn = builder.Configuration.GetSection("Sentry:Dsn").Value;
        var environment = builder.Configuration["Sentry:Environment"];
        if (!string.IsNullOrWhiteSpace(environment) && !environment.Contains('#'))
            options.Environment = environment;
        ...
    });
}
```

`appsettings.json` (linhas 21-26):

```json
"Sentry": {
  "Dsn": "#{SENTRY_DSN}#",
  "Environment": "#{ENVIRONMENT}#",
  "Debug": "#{SENTRY_DEBUG}#",
  "Profiling": "#{SENTRY_PROFILING}#"
}
```

Os `#{...}#` são **tokens de deploy** substituídos por ambiente na release. O `if (sentryEnabled)`
só liga o Sentry se o token `#{SENTRY_DSN}#` virou um DSN real.

### Conclusão

A **stage de produção da release do backend não injeta `SENTRY_DSN`** → o placeholder permanece literal
→ `sentryEnabled = false` → `UseSentry()` nunca é chamado → Sentry **completamente desligado** em produção.

- **Não é problema de código nem de SDK:** em `hml` o backend reporta erros e transações normalmente.
- **Não é só tracing:** se faltasse apenas `TracesSampleRate`, haveria *erros* em prd sem transações. Como há **zero de tudo**, o gate do DSN é o culpado.
- O frontend funciona em prod porque a release **dele** injeta o DSN de produção — diferença de configuração por produto, não de código.

### Correção (variable group da stage PROD do backend)

1. **`SENTRY_DSN`** → DSN do projeto `autoloadv4-backend` (crítico; sem isso nada liga).
2. **`ENVIRONMENT`** → deve resolver para `prd` (senão `options.Environment` fica vazio).
3. **`Sentry__TracesSampleRate`** → confirmar como env var (não há token p/ ele no `appsettings`; em dev o tracing só funciona porque a var é injetada no deploy). Sem ela: erro sim, transação/view não.

---

## Brindes / itens colaterais

- **Portal-cliente** (`autoloadv4-portal-cliente`): só 28 eventos, todos em `development`. Praticamente sem uso / sem produção.
- **EdgeGateway** (`autoloadv4-edgegateway`): zero transações. Provável mesmo gap de DSN na release.
- **Tags de ambiente inconsistentes:** frontend tem `prd` **e** `production` (órfão); backend tem `dev` **e** `Development`. Padronizar para um valor único por ambiente — quick win de higiene.
- O endpoint backend mais chamado (todos ambientes) é `GET /v1/InventoryCutoffs/alerts` (16.166) — **polling automático**, não uso humano; candidato a otimização.

---

## Próximos passos

- [ ] **Abrir item no board** (Azure DevOps `AUTOLOAD_V4`, tipo Bug) — **pendente**: o PAT atual (`.azdo_pat.txt`) só tem escopo de leitura; create de Work Item retorna 401 no MCP e no REST. Requer PAT com *Work Items (Read & Write)*. Conteúdo do ticket já redigido nesta investigação.
- [ ] Time de DevOps adiciona `SENTRY_DSN`/`ENVIRONMENT`/`Sentry__TracesSampleRate` na stage prod do backend.
- [ ] Repetir o check em portal-cliente e edgegateway.
- [ ] Padronizar tags de ambiente nos 4 projetos.
