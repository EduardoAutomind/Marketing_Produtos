# AutoLoad V4 — Documentação Técnica

> Plataforma **enterprise de gestão e automação para terminais de granéis líquidos**
> (combustíveis, químicos, óleos): do agendamento de veículos ao **controle em tempo real do
> carregamento via automação industrial**.

Última revisão: 2026-05-28 · Organização Sentry: `automind-qd`

---

## 1. Visão geral

O AutoLoad V4 é organizado em dois módulos de negócio sobre um **Core** compartilhado:

- **Management** — gestão, agendamento e estoque (cadastro de veículos/motoristas, slots, grupos, agendamentos, ativos do terminal).
- **Operations** — execução autônoma das operações no terminal (programs, operations, transactions, manifests).

Diferencial central: **edge computing real** — o Edge Gateway opera offline no terminal e sincroniza com o backend quando há conectividade.

### Princípios arquiteturais

| Princípio | Aplicação |
|---|---|
| DDD | Domínios bem definidos (Management, Operations, Core) |
| Multi-Tenancy | **Database-per-tenant** (isolamento total entre clientes) |
| API-First | 52 controllers v1 + 1 v2, versionado por URL |
| Real-Time | 3 SignalR Hubs (telemetria, mensagens, heartbeats) |
| Edge Computing | Gateway autônomo nos terminais com scripts Lua |

---

## 2. Stack & componentes deployáveis

São **4 deployáveis** principais, cada um com seu projeto Sentry correspondente:

| Componente | Tecnologia | Projeto Sentry | Papel |
|---|---|---|---|
| Backend | .NET 8 / ASP.NET Core 8, EF Core 8, SignalR, MQTT | `autoloadv4-backend` | API REST (52 controllers v1), regras de negócio, real-time, dispatch MQTT |
| Frontend | Next.js 14 (App Router), React 18, TypeScript, Tailwind, Radix, Zustand | `autoloadv4-frontend` | Web admin + portais self-service + dashboard tempo real |
| **Edge Gateway** | .NET 8 Worker Service (Windows/Linux), MQTTnet, NLua | `autoloadv4-edgegateway` | Automação industrial **no terminal**: drivers, scripts Lua, telemetria |
| Kiosk | React/Vite | (frontend) | Check-in/check-out simplificado no terminal |

**Banco de dados:** PostgreSQL (primário). SQL Server suportado como fallback.
**CI/CD:** Azure Pipelines.

---

## 3. Multi-tenancy (database-per-tenant)

Diferente do AutoChecker (que usa schema-per-tenant), o AutoLoad V4 isola cada cliente em **um banco PostgreSQL distinto**:

- **`AutoloadContext`** → banco global `autoload` (9 tabelas):
  `Tenants`, `Users`, `TenantUsers`, `UserSessions`, `AuditTrails`, `ScheduledJobs`, `JobExecutions` (entre outras).
- **`TenantContext`** → banco `autoload_<TENANT_ID>` por tenant (~83 tabelas: domínios Management + Operations + Core).

Resolução do tenant por requisição via `SchemaHeaderMiddleware` + `TenantProvider`:

1. Header HTTP `X-Tenant-Id`, **ou**
2. Claim `tenant_id` no JWT.

Isolamento total — não há vazamento de dados entre clientes. **Total: ~92 tabelas** (9 globais + 83 por tenant).

> O tenant master `autoload` tem regras especiais (administração cross-tenant, gestão de tenants).

---

## 4. Comunicação (3 caminhos)

Toda telemetria e todos os comandos trafegam por um destes três caminhos:

```
Frontend ⇄ Backend : REST (/api/*) + SignalR (/hubs/*) ; JWT Bearer
Backend  ⇄ EdgeGw  : MQTT  (autoload/gateway/{id}/{telemetry|command|rpc/request|rpc/response})
EdgeGw   ⇄ campo   : Serial (RS-232/485) / TCP-IP / OPC UA / ModBus TCP
```

### SignalR Hubs (3)

| Hub | Endpoint | Conteúdo |
|---|---|---|
| `TelemetryHub` | `/hubs/telemetry` | Telemetria de dispositivos (vazão, totalizadores, status) |
| `MessageHub` | `/hubs/messages` | Mensagens de negócio (autorização, alertas, status de programa) |
| `HeartbeatHub` | `/hubs/heartbeats` | Conectividade de gateways e dispositivos |

### Background workers no backend (3)

| Worker | Função |
|---|---|
| `JobExecutionWorker` | Executa jobs agendados (`ScheduledJobs` → `JobExecutions`) |
| `MQTTWorker` | Consome filas MQTT vindas dos Edge Gateways |
| `ProgramWorker` | Avança máquinas de estado de Program / Operations / Transactions |

### Tópicos MQTT (Backend ⇄ Edge Gateway)

```
autoload/gateway/{gatewayId}/telemetry         # gateway → backend
autoload/gateway/{gatewayId}/command           # backend → gateway
autoload/gateway/{gatewayId}/rpc/request       # backend → gateway (RPC)
autoload/gateway/{gatewayId}/rpc/response      # gateway → backend (RPC)
```

Em HML/PRD o broker MQTT opera com **TLS**. Em DEV é opcional.

---

## 5. Edge Gateway & drivers

O Edge Gateway é a peça que justifica o "edge computing" — um **.NET 8 Worker Service** rodando no terminal, fazendo a ponte entre o backend e os equipamentos físicos.

> **Esta é a fonte central de erros do projeto `autoloadv4-edgegateway` no Sentry.**

### Arquitetura de drivers

- **16 drivers** em 6 categorias, registrados em `DeviceDrivers.json` e instanciados por **reflection**.
- Todos implementam a interface `IDriver` (lifecycle + telemetria) sobre a classe abstrata `Driver`.
- Princípios:
  - **Thread-safe** via `SemaphoreSlim`.
  - **Reconexão automática** — `EnsureConnected()` é chamado antes de cada I/O.
  - **Cancelamento cooperativo** via `StopRequested`.
  - **Logging estruturado** (com correlação por driver/dispositivo).

### Catálogo de drivers

| Categoria | Drivers | Protocolo | Interface |
|---|---|---|---|
| **Preset** (loaders) | Accuload 3/4, Danload 6000/8000, Fusion4, Microload, TCC, Mock | Serial/TCP, frames STX/ETX/LRC (Accuload), Modbus/TCP (Fusion4) | `IDriverPreset` (baixo nível) + `IPresetDriverV4` (alto nível p/ Lua) |
| **OPC** | OPC Client (+Mock) | OPC UA (`opc.tcp://`) | `IVariableDriver` |
| **ModBus** | ModBus Client (+Mock) | ModBus TCP | `IVariableDriver` |
| **Display** | Spider | TCP (binário) | `IDisplayDriver` |
| **TruckScale** | Toledo (IND560/8540) | Serial/TCP | `ITruckScaleDriver` |
| **UCA** (controle de acesso) | Unidata 330 (+Mock) | TCP | `IDriverUCA` |

### Threads do gateway

| Thread | Cardinalidade | Função |
|---|---|---|
| `GatewayWorker` | 1 | Consome/produz MQTT |
| `HeartbeatThread` | 1 | Publica status do gateway a cada 1s |
| `TelemetryThreads` | 1 por dispositivo | Coleta telemetria via `GetTelemetryData` |
| `ProcessThreads` | 1 por processo ativo | Executa **scripts Lua** que orquestram o carregamento |

### Scripts Lua (orquestração do carregamento)

Os `ProcessThreads` executam scripts Lua (via NLua) que definem o ciclo de carregamento:

```
AuthorizeLoading  → libera o preset para iniciar
WaitLoading       → acompanha vazão e totalizadores em tempo real
FinalizeLoading   → fecha transação, sincroniza com backend
```

Os scripts têm acesso aos drivers de alto nível (`IPresetDriverV4`, `IDisplayDriver`, `ITruckScaleDriver`, etc.) — toda lógica de negócio do carregamento mora no Lua, não no C#.

### Erros típicos (Sentry `autoloadv4-edgegateway`)

- Falha/timeout de comunicação com dispositivo (geralmente segue de reconexão).
- Gateway offline (visível no `HeartbeatHub` — o backend perde os pings de 1s).
- Driver não elegível para automação (configuração inválida em `DeviceDrivers.json`).
- Problemas de protocolo serial (frames STX/ETX/LRC mal formados em Accuload).
- Exceções dentro de scripts Lua.

> **Resiliência:** erro isolado de driver **não** derruba o gateway inteiro. Drivers Mock e simuladores standalone (OPC UA, TruckScale, UCA) permitem testar todo o fluxo sem hardware físico.

---

## 6. Domínios & máquinas de estado

### Management

- **Vehicles / Drivers** — workflow `PENDING → APPROVED / REJECTED`.
- **VehicleCompositions** — composições veiculares (cavalo + reboques + tanques).
- **Appointments** — agendamentos compostos por:
  - **Slots** — janelas de tempo da baia.
  - **Grupos** — agrupamento de slots.
  - **Agendamentos** — a reserva propriamente dita.

Máquina de estado do agendamento:

```
RESERVED → APPROVED → CONFIRMED → IN_PROGRESS → COMPLETED
                                      ↓
                  EXPIRED | NO_SHOW | CANCELED  (por timeout/manual)
```

Alocação de slot é **"As Soon As Possible"** (busca o próximo horário disponível compatível).

### Operations

- **Program** — guarda-chuva da operação. Máquina:
  ```
  DRAFT → APPROVED → CONFIRMED → IN_PROGRESS → CLOSING → COMPLETED
  ```
- **Operations** — operações individuais dentro de um Program.
- **Transactions** — execução física do carregamento:
  ```
  IDLE → AUTHORIZED → LOADING → LOADED
                ↓        ↓
              ABORTED  PAUSED
  ```
- **Manifests** — documento fiscal/operacional consolidado.
- **Ativos do terminal:** Bays, StorageTanks, Circuits, Pipelines, Pumps, Presets.
- **Infra física:** Gateways, Devices.

### RBAC

- **55 permissões** distribuídas em **13 módulos**.
- Escopadas por **organização** (hierarquia via `HierarchyPath`).

---

## 7. Integrações & serviços externos (10)

| # | Serviço | Uso |
|---|---|---|
| 1 | REST API | 52 controllers v1 + 1 v2, versionado por URL (`/v1/...`) |
| 2 | SignalR | 3 hubs (telemetria, mensagens, heartbeats) |
| 3 | **MQTT** | Comunicação com Edge Gateways (TLS em HML/PRD) |
| 4 | **MailKit / Brevo** | Envio de email |
| 5 | **Zenvia** (SMS) | Notificações via SMS (jobs assíncronos) |
| 6 | **Zenvia** (WhatsApp) | Notificações via WhatsApp (jobs assíncronos) |
| 7 | **OCI Object Storage** | Storage em PRD/HML (Local em DEV, Database como fallback) |
| 8 | **Sentry** | Observabilidade (DEV opcional, HML ativo, PRD ativo + profiling) |
| 9 | **LDAP / AD** | Autenticação corporativa |
| 10 | Webhooks de saída | Por programa, via `ProgramWebhookService` |

### Webhooks de entrada (status delivery)

```
POST /v1/webhooks/events/sms
POST /v1/webhooks/events/whatsapp
```

> **SERPRO não é integração do AutoLoad V4** — isso é AutoChecker. Não confundir.

### Swagger

Documentação OpenAPI publicada **por versão × idioma** (pt-BR / en).

---

## 8. Autenticação

### Modos por tenant (`auth_mode`)

| Modo | Descrição |
|---|---|
| `Basic` | Usuário + senha |
| `2FA` | Código de 6 dígitos enviado por email |
| `AD/LDAP` | Integração corporativa |
| `OAuth` | Placeholder (não implementado em produção) |

### Mecanismos transversais

- **JWT Bearer** — HMAC-SHA256, validade 24h.
- **Negotiate** — Windows / Kerberos para ambientes corporativos.
- **API Keys** — autenticação machine-to-machine.
- **Sessões** rastreadas por **JTI** em `UserSession` (single-login ou multi-login configurável por tenant).
- **Senhas** armazenadas com **PBKDF2-SHA256**.

---

## 9. Deploy & ambientes

```
Cloudflare (CDN/WAF)
   │
   ├── DigitalOcean App Platform   → frontend (Next.js)
   └── DigitalOcean Droplets       → backend (.NET 8, IIS / kestrel)
                                       └── PostgreSQL gerenciado + Redis
                                       
Terminais físicos                   → Edge Gateway (Windows Service / Linux daemon)
```

### Ambientes

| Ambiente | Branch | Sentry | Profiling |
|---|---|---|---|
| DEV | `develop` | Opcional | — |
| HML | `release/*` | Ativo | — |
| PRD | `master` | Ativo | **Ativado** |

### Fluxo de release

- **Git Flow** + hotfix com **backport obrigatório** para `develop`.
- Variáveis de configuração via placeholders `#{VAR}#` substituídos no pipeline de release.
- Frontend lê configuração em runtime via `public/env.json` (não embute em build).
- Release Sentry definida via variável `SENTRY_RELEASE` (formato `backend@<hash>` / `frontend@<hash>` / `edgegateway@<hash>`).

### Repositório

Monorepo com pastas:

```
Backend/        # .NET 8 (API)
Frontend/       # Next.js 14
EdgeGateway/    # .NET 8 Worker Service
Kiosk/          # React/Vite
DevOps/         # Templates Azure Pipelines, scripts de release
```

---

## 10. Observabilidade

### Projetos Sentry

| Componente | Projeto | Origem dos erros |
|---|---|---|
| Backend .NET | `autoloadv4-backend` | API, workers, regras de negócio, MQTT dispatch |
| Frontend Next.js | `autoloadv4-frontend` | Erros de runtime no navegador + SSR |
| Edge Gateway | `autoloadv4-edgegateway` | Drivers, scripts Lua, MQTT, comunicação com campo |

### Como mapear uma issue do Sentry → componente

- **`autoloadv4-edgegateway`** → quase sempre driver, protocolo serial, OPC/Modbus, ou script Lua.
  Consultar threads `TelemetryThreads` / `ProcessThreads` na issue.
- **`autoloadv4-backend`** → controller REST, worker, SignalR hub, EF Core, dispatch MQTT.
  A tag `tenant_id` indica o banco impactado.
- **`autoloadv4-frontend`** → React/Next.js. Stack trace aponta a rota; cross-check com `release` (`frontend@<hash>`).

> Erros de campo (físicos) sempre aparecem primeiro em `autoloadv4-edgegateway`; eles podem **secundariamente** gerar issues no `autoloadv4-backend` se o backend ficar esperando uma resposta MQTT que nunca volta. Investigue do edge para dentro.

---

## 11. Resumo de contadores (referência rápida)

| Item | Quantidade |
|---|---|
| Controllers v1 | 52 |
| Controllers v2 | 1 |
| SignalR Hubs | 3 |
| Background workers (backend) | 3 |
| Integrações externas | 10 |
| Drivers (Edge Gateway) | 16 |
| Categorias de drivers | 6 |
| Threads no Edge Gateway | 4 tipos (1 + 1 + N + N) |
| Modos de autenticação | 4 |
| Provedores de storage | 3 (OCI, Local, Database) |
| Idiomas suportados | 2 (pt-BR, en) |
| Tabelas globais (`autoload`) | 9 |
| Tabelas por tenant | ~83 |
| **Total de tabelas** | **~92** |
| Permissões RBAC | 55 |
| Módulos RBAC | 13 |

---

## 12. Referências cruzadas

- **Skill `produtos-automind`** → `.claude/skills/produtos-automind/references/autoload-v4.md` (versão condensada para uso da IA).
- **Skill `analise-sentry`** → análise ad-hoc do estado atual das issues.
- **Dashboard Sentry** → `dashboard-sentry.html` (raiz do repositório).
- **Auditoria de observabilidade** → `Estudo de melhoria de observabilidade/Auditoria_Observabilidade_AutoLoadV4_2026-05-28.md`.
- **Guia de troubleshooting** → `Estudo de melhoria de observabilidade/Guia_Troubleshooting_Sentry_AutoLoad_V4.md`.
- **Oportunidades de melhoria** → `Estudo de melhoria de observabilidade/Oportunidades de Melhoria de Observabilidade - Autoload V4.md`.
- **Diagnóstico Accuload IV / Edge Gateway** → `Accuload/` (raiz).
- **ExoBrain:** `/Automind/Produtos/AutoLoad V4.md`.
