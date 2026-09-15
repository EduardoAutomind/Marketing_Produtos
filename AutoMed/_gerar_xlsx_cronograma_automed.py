# -*- coding: utf-8 -*-
"""Gera o XLSX do cronograma de observabilidade do AUTOMED.

Mesmo modelo visual dos cronogramas do AutoLoad V4 e do AutoChecker (capa navy,
barras de onda coloridas, coluna # como espinha colorida, fills de esforço/status,
aba Legenda, dropdown + formatação condicional de status), com conteúdo do Automed
fundamentado em TRÊS fontes cruzadas:

  - DOC      — documentação técnica do Automed (.NET 8 / ASP.NET Core; Angular 13;
               SQL Server/Azure SQL híbrido relacional+JSON; 3 Windows Services —
               Sync.Worker [XConnect/PI System/Scan], Tasks.Worker [fila a cada 5s],
               FileExporter.Worker [diário]; conformidade ANP via i-Engine SOAP;
               multi-tenant por OrganizacaoId + schema por organização).
  - SENTRY   — snapshot ao vivo do projeto `automed` (org automind-qd), janela
               01→07/06/2026: 18 issues, 0 resolvidas, platform dotnet-aspnetcore,
               UM único environment ('production'), hasMonitors=False, projeto FORA
               de qualquer regra de alerta. firstEvent 2026-04-14.
  - ESTÁTICO — "Oportunidades de Melhoria de Observabilidade - Automed.md"
               (14/04/2026, 12 itens).

Correção de premissa central (validada contra o Sentry):
  - O estudo estático de abril dizia "Sentry NÃO está instalado em NENHUM componente".
    REALIDADE: o Sentry JÁ está instalado e capturando na API (.NET) desde 14/04/2026
    (projeto `automed`). O esforço muda de "instalar do zero" para "sanear o que já
    captura + estender cobertura a Workers e Frontend (ainda cegos)".

Decisões desta versão (espelham AutoChecker):
  - Responsável = "A definir" em todas as linhas (equipe ainda não atribuída).
  - Semanas RELATIVAS (Sem 1..14) — sem datas absolutas de calendário.
  - Só abas Cronograma + Legenda (Automed não tem ata própria).

Como rodar:
  python "Cronograma Observabilidade/AutoMed/_gerar_xlsx_cronograma_automed.py"
"""

from __future__ import annotations

from pathlib import Path

from openpyxl import Workbook
from openpyxl.formatting.rule import CellIsRule
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "Cronograma_Observabilidade_Automed_2026-06-08.xlsx"

# ── Paleta (espelha os demais cronogramas) ───────────────────────────────
NAVY      = "1E3A5F"
SLATE     = "334155"
SUBTITLE  = "94A3B8"
DARK      = "1E293B"
WHITE     = "FFFFFF"
ZEBRA     = "F8FAFC"
LILAC     = "EDE9FE"   # coluna Camada

# fills de esforço
ESF = {"P": "DBEAFE", "M": "FEF9C3", "G": "FED7AA"}
# fills de status
STATUS_FILL = {
    "Não iniciado": "E2E8F0",
    "Em andamento": "FEF9C3",
    "Concluído":    "DCFCE7",
    "Bloqueado":    "FEE2E2",
    "Pendente":     "FEF3C7",
}
STATUS_OPCOES = ["Não iniciado", "Em andamento", "Concluído", "Bloqueado", "Pendente"]

# cor de cada onda — progressão do gradiente da marca AutoMind (rosa → navy)
ONDA_COR = {
    0: "FA094E",  # rosa — gate crítico de saneamento
    1: "CF1A66",
    2: "940755",  # magenta
    3: "6F1170",
    4: "44055A",  # roxo
    5: "231A66",
    6: "03045E",  # navy
}

CAL = "Calibri"


def fill(hex_):
    return PatternFill("solid", fgColor=hex_)


# ── Conteúdo do cronograma ───────────────────────────────────────────────
# Cada onda: (numero, titulo_barra, [itens])
# item: (titulo, descricao, camada, esforco, sem_ini, sem_fim, responsavel, status, obs)
# "camada" = componente/projeto Sentry do Automed.

RESP = "A definir"

ONDAS = [
    (0, "ONDA 0 — Saneamento da Base  (Semanas 1–2)  ·  GATE: nada de ampliação antes disto", [
        ("Padronizar environment + isolar DEV/QA/HOMOLOG/PRD no projeto automed",
         "Hoje o projeto `automed` no Sentry tem UM único environment: 'production'. Os ambientes LOCAL/DEVELOPMENT/QA/"
         "HOMOLOG (TAF/TAC) existem no produto (appsettings 'Ambientes') mas ou não enviam ao Sentry ou caem todos como "
         "'production'. Configurar options.Environment a partir de ASPNETCORE_ENVIRONMENT/config e garantir que só PRD "
         "popule o projeto produtivo — qualquer painel/alerta sobre base contaminada por não-produção é sem sentido.",
         "API", "M", "Sem 1", "Sem 1", RESP, "Não iniciado",
         "SENTRY: project.environments = ['production'] apenas. KPI: ≥99% dos eventos com environment correto em 7 dias."),
        ("Padronizar release (AppVersion) + associar a deploy/commits do Azure DevOps",
         "Definir options.Release = AppVersion de forma consistente na API e (depois) nos Workers/Frontend, e associar o "
         "release ao deploy para habilitar suspect commits e correlação picos×deploy. Os stacktraces mostram caminhos de "
         "build do Azure DevOps (D:/Agents/DevopsService/AgentBuild1|2/...) — há mais de um agente/branch publicando; sem "
         "release consistente não dá para saber qual versão gerou o erro.",
         "API", "M", "Sem 1", "Sem 1", RESP, "Não iniciado",
         "ESTÁTICO item #1 (Sentry:Release=#{AppVersion}#). CÓDIGO: builds AgentBuild1 e AgentBuild2 coexistindo."),
        ("Corrigir schema drift de colunas (AceitoUsuario, enviado) — migração EF não aplicada",
         "Maior cluster da semana: o código referencia colunas que NÃO existem no banco — 'Invalid column name AceitoUsuario' "
         "(AUTOMED-Z, 185 ev) + 'KeyNotFoundException aceitoUsuario' no NotificacaoDAL.RowToNotificacao (AUTOMED-10, 57 ev) "
         "+ 'Invalid column name enviado' (AUTOMED-Y, 5 ev). Causa típica: código publicado à frente da migração EF Core / "
         "migração não aplicada em produção. Alinhar migração×deploy e adicionar gate que falha o deploy com migração pendente.",
         "Models / DB", "M", "Sem 1", "Sem 2", RESP, "Não iniciado",
         "SENTRY: AUTOMED-Z 185 + AUTOMED-10 57 + AUTOMED-Y 5 = ~247 ev. Maior fonte de ruído. Bug corrigível."),
        ("Aplicar migrações faltantes nos schemas por organização (tabela 'monitoramentos' ausente)",
         "'Invalid object name <hash>.monitoramentos' em Sql.Execute (AUTOMED-A 47 ev + AUTOMED-2 24 ev): a tabela não existe "
         "em um schema de organização (ex.: db5cd138903b59527ee0c4840913c0b8). O Automed é multi-tenant com SCHEMA POR "
         "ORGANIZAÇÃO — a migração não chegou a esse schema. Garantir que o deploy aplique migrações a TODOS os schemas de "
         "organização (análogo ao migrate_schemas do AutoChecker) e adicionar verificação por organização.",
         "Models / DB", "M", "Sem 1", "Sem 2", RESP, "Não iniciado",
         "SENTRY: AUTOMED-A 47 + AUTOMED-2 24 = 71 ev. Schema por organização confirmado (hash no nome do objeto)."),
        ("Filtrar/corrigir ruído de host (Cannot determine the https port) — HttpsRedirection",
         "Maior ruído de UM único issue: 'InvalidOperationException: Cannot determine the https port from "
         "IServerAddressesFeature' no HttpsRedirectionMiddleware (AUTOMED-1, 107 ev). É erro de configuração de hosting "
         "(porta HTTPS não resolvida atrás do proxy/Kestrel). Configurar HTTPS port (UseHttpsRedirection/ForwardedHeaders) "
         "ou, se for esperado atrás de TLS-terminating proxy, descartar via before_send / Inbound Filter.",
         "API", "P", "Sem 2", "Sem 2", RESP, "Não iniciado",
         "SENTRY: AUTOMED-1 107 ev — maior issue único por volume. Ruído de infra mascarando sinal."),
        ("Reclassificar exceções de domínio esperadas (auth + validação) de error para warning/drop",
         "Várias AutomedException previstas estão sendo capturadas como `error` e inflando o ruído: 'UsuarioSendoUtilizado "
         "(Unauthorized)' no Login (AUTOMED-5, 49 ev), 'EventoNaoExistente (Forbidden)' (AUTOMED-G), 'UsuarioInvalido "
         "(Forbidden)' no ReiniciarSenha (AUTOMED-V), além de validações de negócio (AUTOMED-T 'duas aberturas/fechamentos "
         "consecutivos', AUTOMED-B 'BSWFiscal já cadastrado', AUTOMED-X 'BTP já enviado', AUTOMED-W 'CV não cadastrado'). "
         "Definir o que é erro vs evento esperado e ajustar nível (warning) / before_send.",
         "API", "M", "Sem 2", "Sem 2", RESP, "Não iniciado",
         "SENTRY: AUTOMED-5 49 + G/V/T/B/X/W. AutomedException de fluxo esperado tratada como error."),
        ("Confirmar SendDefaultPii=false + scrubbing de PII/LGPD",
         "O estudo propõe options.SendDefaultPii=false (item 1) e Sentry.setUser({email, organizacao}) no frontend (item 2). "
         "Confirmar que a API NÃO está enviando PII por padrão e definir scrubbing de e-mail/dados de organização e de "
         "qualquer dado sensível de produção (cliente óleo & gás). NUNCA enviar a ConnectionString do XConnect aos eventos.",
         "API / Frontend", "M", "Sem 2", "Sem 2", RESP, "Não iniciado",
         "ESTÁTICO #1/#2 (setUser email) + nota: ConnectionString do XConnect jamais nos breadcrumbs (itens #5/#6)."),
        ("Triagem ZERO do backlog (18 issues, 0 resolvidas)",
         "Classificar todas as issues (Resolved / Ignored com prazo / In Progress) e documentar critério. Hoje há 18 issues "
         "abertas e 0 resolvidas na janela — não há fluxo de triagem ativo. Backlog sem dono contamina qualquer métrica.",
         "Automed", "M", "Sem 2", "Sem 2", RESP, "Não iniciado",
         "SENTRY: 18 unresolved, 0 resolvidas (janela 01–07/06). Sem fluxo de triagem."),
    ]),
    (1, "ONDA 1 — Fundação dos SDKs e Cobertura  (Semanas 3–4)", [
        ("Enriquecer contexto/tags na API (organizacao_id, organizacao_nome, usuario_id)",
         "Sobre o init já existente: adicionar tags globais de tenant no middleware de auth/BaseController a partir das claims "
         "do JWT (OrganizacaoId, OrganizacaoNome, usuario). Hoje TODAS as 18 issues mostram userCount=1 — sinal de que o "
         "contexto de usuário/organização não está populado, então não dá para saber QUAL cliente foi afetado.",
         "API", "M", "Sem 3", "Sem 4", RESP, "Não iniciado",
         "ESTÁTICO item #2. SENTRY: userCount=1 em todas as issues (contexto de tenant ausente)."),
        ("Estender Sentry aos 3 Workers (Sync, Tasks, FileExporter) — hoje no Windows Event Viewer",
         "A doc indica que os Workers logam no WINDOWS EVENT VIEWER, não no Sentry — porém alguns erros de processos do "
         "Tasks.Worker JÁ aparecem (Automind.Automed.Tasks.Core/Processos/...). Confirmar e completar a cobertura dos 3 "
         "Windows Services: Sync.Worker (XConnect/PI System/Scan), Tasks.Worker (fila a cada 5s) e FileExporter.Worker "
         "(diário). Os Workers são 'a fonte principal de erros operacionais' — sem eles no Sentry, falha de sync/ANP some.",
         "Workers", "G", "Sem 3", "Sem 4", RESP, "Não iniciado",
         "DOC: logging dos workers no Event Viewer. SENTRY: já há erros do Tasks.Core; Sync/PI/Scan/FileExporter a confirmar."),
        ("Instrumentar o Frontend Angular 13 (@sentry/angular + ErrorHandler customizado)",
         "Não existe projeto Sentry de frontend (só `automed` dotnet-aspnetcore) — o SPA Angular 13 está CEGO. Instalar "
         "@sentry/angular, init no main.ts com environment/release, ErrorHandler customizado (capturar erros Angular, não só "
         "HTTP) e decidir projeto Sentry próprio (automed-frontend) vs tag. Avaliar Session Replay com masking (PII).",
         "Frontend", "M", "Sem 3", "Sem 4", RESP, "Não iniciado",
         "ESTÁTICO item #1 (npm @sentry/angular). SENTRY: nenhum projeto de frontend existe."),
        ("Documentar política de envio de eventos por camada e por ambiente",
         "Critério de captura por camada (API/Workers/Frontend) e nível mínimo por ambiente (DEV info+debug, "
         "QA/HOMOLOG info+warning+error, PRD warning+error). Definir o que é erro vs evento de negócio esperado — base para "
         "a reclassificação de ruído (auth, validações, ANP rejeitado).",
         "Automed", "P", "Sem 4", "Sem 4", RESP, "Não iniciado",
         "Espelha a política do AutoLoad/AutoChecker. Base para Onda 0 (reclassificação) e Onda 2."),
    ]),
    (2, "ONDA 2 — Contexto e Agrupamento  (Semanas 4–6)", [
        ("Instrumentar o pipeline de Sync de produção (XConnect/PI/Scan) com breadcrumbs",
         "ProducoesService é o coração do produto: lê produção do banco do cliente (XConnect/Weatherford), processa medidores "
         "por equipamento e cria eventos de produção. Adicionar tags sync.unidade_id/unidade_nome/organizacao_id e breadcrumbs "
         "por unidade e por dia processado (qtd de equipamentos) para saber QUAL unidade, QUAL dia e quantos equipamentos "
         "antes de uma falha. Idem PI System (PlotValues, valores congelados) e Scan (CSV OMNI70/711/712).",
         "Sync.Worker", "G", "Sem 4", "Sem 5", RESP, "Não iniciado",
         "ESTÁTICO item #5. Falha de sync = perda de dado de medição (regulatório). Depende da cobertura do Worker (Onda 1)."),
        ("Capturar erros silenciosos nos Workers (catch que só faz LogError)",
         "Os loops dos Workers capturam exceções com Logger.LogError() sem re-lançar nem enviar ao Sentry — falha de sync "
         "com o XConnect ou de tarefa crítica (AtualizarSemaforos, NotificarDesviosMedicao) some silenciosamente. Adicionar "
         "SentrySdk.CaptureException nos catch do Sync.Worker e do Tasks.Worker, com tags worker/tarefa/organizacao_id.",
         "Workers", "M", "Sem 5", "Sem 6", RESP, "Não iniciado",
         "ESTÁTICO itens #3 e #4 (Worker.cs catch LogError sem capture). Detectar antes do cliente."),
        ("Fingerprint + tratamento das exceções recorrentes de cálculo de produção",
         "Erros de cálculo do Tasks.Worker com alto volume e provável causa de CONFIGURAÇÃO faltante por organização: "
         "'Formula para rateio de óleo não cadastrada' (AUTOMED-6, 55 ev, Calculadores.CalcularProducaoPocos) e 'Estado de "
         "operação do poço ... indefinido' (AUTOMED-S, 20 ev). Agrupar por organização/unidade via fingerprint estável e "
         "decidir: é erro de aplicação ou configuração pendente do cliente (vira warning/alerta de config)?",
         "Tasks.Worker", "M", "Sem 5", "Sem 6", RESP, "Não iniciado",
         "SENTRY: AUTOMED-6 55 + AUTOMED-S 20. Alta recorrência; precisa de fingerprint por unidade + decisão config×erro."),
    ]),
    (3, "ONDA 3 — Alertas + Health Checks  (Semanas 6–8)", [
        ("Definir níveis N1/N2/N3 e responsáveis por alerta",
         "Mapear quem recebe qual alerta por nível ANTES de ativar qualquer notificação. Gate da política de alertas. "
         "Considerar a criticidade regulatória (ANP) na priorização — rejeição/prazo perdido tem impacto de multa.",
         "Automed", "M", "Sem 6", "Sem 6", RESP, "Não iniciado",
         "Pré-requisito da ativação dos alertas (espelha AutoLoad/AutoChecker)."),
        ("Configurar regras de alerta com filtro environment:production",
         "Hoje o projeto `automed` NÃO está em NENHUMA regra de alerta (a única regra high-priority cobre autoloadv4-edgegateway "
         "e os projetos do AutoChecker). Criar regras com filtro environment:production, threshold, supressão, alerta de "
         "regressão (resolved→unresolved) e roteamento por nível N1/N2/N3.",
         "Automed", "M", "Sem 6", "Sem 7", RESP, "Não iniciado",
         "SENTRY: combined_rules — `automed` ausente da lista de projetos da regra. Depende do environment saneado (Onda 0)."),
        ("Health Check endpoint (/health) + Uptime Monitor",
         "Não existe endpoint /health na API → não há como configurar o Uptime Monitor do Sentry. Adicionar "
         "AddHealthChecks().AddSqlServer(...) + check de status dos Workers e MapHealthChecks('/health'); configurar Uptime "
         "Monitor sobre ele para detectar API fora do ar antes do cliente.",
         "API", "M", "Sem 7", "Sem 7", RESP, "Não iniciado",
         "ESTÁTICO item #9. Sem endpoint de health hoje."),
        ("Cron Monitors (check-ins) para os 3 Workers",
         "Os 3 Windows Services rodam continuamente (Tasks a cada 5s, FileExporter a cada 24h, Sync por unidade) e, se "
         "travarem, não há detecção. Instrumentar CaptureCheckIn(InProgress/Ok/Error) por ciclo de cada worker para alertar "
         "quando um deles ficar N minutos sem executar. hasMonitors do projeto = False hoje.",
         "Workers", "M", "Sem 7", "Sem 8", RESP, "Não iniciado",
         "ESTÁTICO item #8. SENTRY: project.hasMonitors = False."),
        ("Integração de alertas em canal (Slack/Teams) + ticket + CODEOWNERS",
         "Plugar as regras de alerta num canal (Slack/Teams) e criar ticket automático; configurar CODEOWNERS para "
         "roteamento da issue ao dono. A única regra existente no org notifica por e-mail genérico aos owners — e o `automed` "
         "nem está nela. Definir Slack ou Teams como canal oficial.",
         "Automed", "M", "Sem 8", "Sem 8", RESP, "Não iniciado",
         "Depende de N1/N2/N3 (gate) e das regras com filtro de ambiente. Hoje sem canal."),
    ]),
    (4, "ONDA 4 — Performance + Logs Correlacionados  (Semanas 8–10)", [
        ("Tratar timeouts de SQL + performance monitoring nos endpoints críticos",
         "'SqlException: Execution Timeout Expired' em Sql.FetchAll (AUTOMED-7 3 ev + AUTOMED-4 1 ev) indica query lenta / "
         "falta de índice / contenção. Com TracesSampleRate (já previsto no item 1 do estudo) ativo, instrumentar latência "
         "dos endpoints críticos (/eventos, /entidades) com tag organizacao_id e atacar as queries que estouram timeout.",
         "API", "M", "Sem 8", "Sem 9", RESP, "Não iniciado",
         "SENTRY: AUTOMED-7/4 (Execution Timeout). ESTÁTICO item #11 (perf nos endpoints críticos)."),
        ("Tracing API ↔ Workers (Refit) — propagar trace pelas chamadas POST /eventos",
         "Os Workers consomem a API via Refit + JWT (não acessam o banco direto). Propagar o trace_id da operação do worker "
         "para a chamada HTTP à API (POST /eventos etc.) para seguir um ciclo de sync ponta a ponta: coleta no XConnect/PI → "
         "POST na API → persistência. Hoje não dá para correlacionar a falha do worker com o request na API.",
         "Automed", "M", "Sem 9", "Sem 10", RESP, "Não iniciado",
         "DOC: workers via Refit+JWT. Depende da cobertura dos Workers (Onda 1)."),
        ("Centralizar logs dos Workers e correlacionar com Sentry",
         "Os Workers logam no Windows Event Viewer (Application Log, source 'Automind.Automed.Sync.PI [Ambiente] [Versão]') — "
         "sem agregação central nem correlação com o erro no Sentry. Definir destino centralizado (ex.: Application Insights/"
         "Seq/ELK) e incluir trace_id para saltar do erro no Sentry ao log estruturado da mesma execução. (AutoChecker tem "
         "Loki/Promtail; o Automed ainda não tem equivalente.)",
         "Workers", "G", "Sem 9", "Sem 10", RESP, "Não iniciado",
         "DOC: logs no Event Viewer, sem agregação. Gap vs AutoChecker (que já tem Loki)."),
    ]),
    (5, "ONDA 5 — Métricas de Negócio + Dashboard  (Semanas 10–12)", [
        ("Definir métricas de negócio do Automed",
         "Volume de produção sincronizada/dia por unidade e por organização; arquivos ANP gerados/enviados/aceitos/"
         "aceito_parcial/rejeitados; latência do ciclo de sync (XConnect/PI/Scan); tarefas executadas vs não executadas "
         "(Tasks.Worker); notificações de desvio enviadas; tempo até envio à ANP. Base para SLAs por organização.",
         "Automed", "M", "Sem 10", "Sem 11", RESP, "Não iniciado",
         "Indicadores derivados dos 3 workers + fluxo ANP. Base para SLA por organização."),
        ("Dashboard por organização e por fluxo (Sync → Tasks → ANP)",
         "Dashboard por ORGANIZAÇÃO (tenant) e por FLUXO de negócio (coleta/sync → fila de tarefas → geração/validação/envio "
         "ANP), não por módulo técnico. Semáforo de saúde do sync por unidade e do envio ANP por organização — exibível para "
         "liderança e suporte.",
         "Automed", "G", "Sem 11", "Sem 12", RESP, "Não iniciado",
         "Consome as métricas do item anterior + instrumentação do pipeline (Onda 2). Exibível na TV do suporte."),
    ]),
    (6, "ONDA 6 — Endurecimento, Regulatório e Compliance  (Semanas 12–14)", [
        ("Rastreabilidade do fluxo ANP (Validar → Gerar → Enviar → Situação)",
         "O motivo de existir do produto: AnpService integra o i-Engine da ANP (SOAP/XML). Instrumentar o ciclo "
         "ArquivoAnp carregado → ValidarArquivoAnp → válido/inconsistente → EnviarArquivo → enviado/rejeitado → "
         "AtualizarSituacaoArquivo (aceito/aceito_parcial/rejeitado). Tratar 'Arquivo Inválido' (AUTOMED-C), 'BTP já enviado' "
         "(AUTOMED-X) e 'BSWFiscal já cadastrado' (AUTOMED-B) com contexto; alertar rejeição/prazo perdido como evento de "
         "NEGÓCIO (impacto de multa/auditoria), mesmo com volume baixo.",
         "Tasks.Worker", "M", "Sem 12", "Sem 12", RESP, "Não iniciado",
         "SENTRY: AUTOMED-C/X/B. DOC: erro regulatório tem impacto de multa mesmo com volume baixo. ESTÁTICO item #7."),
        ("Monitorar conectividade XConnect/PI por organização",
         "A sync depende de uma ConnectionString SQL Server por organização (configuracao.XConnect.ConnectionString) e do PI "
         "AF Server. Se a rede do cliente cair ou a senha mudar, o sync falha sem alerta. Capturar SqlException de conexão "
         "como evento com tags sync.tipo/organizacao/unidade e sql.error_number — SEM logar a connection string.",
         "Sync.Worker", "M", "Sem 12", "Sem 13", RESP, "Não iniciado",
         "ESTÁTICO item #6. Diagnóstico remoto por organização sem acesso ao ambiente do cliente."),
        ("Rastrear notificações de desvio de medição + importação de arquivos ANP",
         "NotificarDesviosMedicao (Tasks.Worker) avisa quando medições desviam de limites regulatórios e ImportarArquivoAnp "
         "processa arquivos da ANP. Adicionar breadcrumbs/contexto (organizacao, tipo, arquivo) e capturar falhas — "
         "evidência de que o sistema notificou/importou corretamente em caso de questionamento regulatório.",
         "Tasks.Worker", "M", "Sem 13", "Sem 13", RESP, "Não iniciado",
         "ESTÁTICO itens #7 e #10. Rastreabilidade para auditoria/conformidade ANP."),
        ("Endurecimento de segurança adjacente (brute-force no login, CORS por organização)",
         "A API tem rate limiting de 5 tentativas de login/min por IP; tentativas bloqueadas são descartadas sem visibilidade "
         "(ataque distribuído passa despercebido) — capturar 429 como warning com o IP. O volume de 'UsuarioSendoUtilizado' "
         "(AUTOMED-5, 49 ev) no Login também merece análise. Revisar CORS configurável por organização. Priorizar com o time "
         "de segurança.",
         "API", "M", "Sem 13", "Sem 14", RESP, "Não iniciado",
         "ESTÁTICO item #12 (rate limit login). SENTRY: AUTOMED-5 49 ev no Login."),
    ]),
]


# ── Aba Cronograma ───────────────────────────────────────────────────────

def montar_cronograma(wb: Workbook) -> None:
    ws = wb.active
    ws.title = "Cronograma"

    larguras = {"A": 4, "B": 36, "C": 60, "D": 16, "E": 10,
                "F": 12, "G": 12, "H": 14, "I": 16, "J": 50}
    for col, w in larguras.items():
        ws.column_dimensions[col].width = w

    # Linha 1 — título
    ws.merge_cells("A1:J1")
    c = ws["A1"]
    c.value = "CRONOGRAMA DE OBSERVABILIDADE — AUTOMED"
    c.fill = fill(NAVY); c.font = Font(name=CAL, size=18, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 30

    # Linha 2 — subtítulo
    ws.merge_cells("A2:J2")
    c = ws["A2"]
    c.value = ("Produto: Automed (API .NET 8 · 3 Workers Windows Service · frontend Angular 13 · SQL Server/Azure SQL · ANP/i-Engine)      "
               "Ferramenta: Sentry      Base: doc técnica + snapshot Sentry 01–07/06/2026 (18 issues) + estudo estático 14/04")
    c.fill = fill(NAVY); c.font = Font(name=CAL, size=10, color=SUBTITLE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[2].height = 18

    # Linha 3 — barra fina
    ws.merge_cells("A3:J3")
    ws["A3"].fill = fill(SLATE)
    ws.row_dimensions[3].height = 6

    # Linha 4 — cabeçalho
    headers = ["#", "Onda / Atividade", "Entrega / Descrição", "Camada", "Esforço",
               "Semana Início", "Semana Fim", "Responsável", "Status", "Observações / Evidência"]
    for i, h in enumerate(headers, start=1):
        cell = ws.cell(row=4, column=i, value=h)
        cell.fill = fill(NAVY)
        cell.font = Font(name=CAL, size=11, bold=True, color=WHITE)
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
    ws.row_dimensions[4].height = 28
    ws.freeze_panes = "A5"

    linha = 5
    contador = 0
    status_ranges = []
    zebra_idx = 0
    for numero, titulo_barra, itens in ONDAS:
        cor = ONDA_COR[numero]
        ws.merge_cells(start_row=linha, start_column=1, end_row=linha, end_column=10)
        b = ws.cell(row=linha, column=1, value="  " + titulo_barra)
        b.fill = fill(cor); b.font = Font(name=CAL, size=11, bold=True, color=WHITE)
        b.alignment = Alignment(horizontal="left", vertical="center")
        ws.row_dimensions[linha].height = 22
        linha += 1

        for titulo, desc, camada, esf, ini, fim, resp, status, obs in itens:
            contador += 1
            base = WHITE if zebra_idx % 2 == 0 else ZEBRA
            zebra_idx += 1
            row_vals = [contador, titulo, desc, camada, esf, ini, fim, resp, status, obs]
            for col, val in enumerate(row_vals, start=1):
                cell = ws.cell(row=linha, column=col, value=val)
                cell.font = Font(name=CAL, size=10,
                                 bold=(col in (1, 2)),
                                 color=(WHITE if col == 1 else DARK))
                halign = "left" if col in (2, 3, 10) else "center"
                cell.alignment = Alignment(horizontal=halign, vertical="top", wrap_text=True)
                if col == 1:                 # espinha colorida da onda
                    cell.fill = fill(cor)
                elif col == 4:               # camada
                    cell.fill = fill(LILAC)
                elif col == 5:               # esforço
                    cell.fill = fill(ESF.get(esf, base))
                elif col == 9:               # status
                    cell.fill = fill(STATUS_FILL.get(status, base))
                else:
                    cell.fill = fill(base)
            status_ranges.append(linha)
            ws.row_dimensions[linha].height = 64
            linha += 1

    ultima = linha - 1

    dv = DataValidation(type="list",
                        formula1='"' + ",".join(STATUS_OPCOES) + '"',
                        allow_blank=False)
    dv.errorTitle = "Status inválido"
    dv.error = "Use um dos valores da lista"
    for r in status_ranges:
        dv.add(f"I{r}")
    ws.add_data_validation(dv)

    fcolors = {
        "Concluído":    ("DCFCE7", "166534"),
        "Em andamento": ("FEF9C3", "854D0E"),
        "Bloqueado":    ("FEE2E2", "991B1B"),
        "Pendente":     ("FEF3C7", "92400E"),
        "Não iniciado": ("E2E8F0", "334155"),
    }
    rng = f"I5:I{ultima}"
    for valor, (fg, fc) in fcolors.items():
        ws.conditional_formatting.add(
            rng,
            CellIsRule(operator="equal", formula=[f'"{valor}"'],
                       fill=fill(fg),
                       font=Font(name=CAL, size=10, bold=True, color=fc)),
        )


# ── Aba Legenda e Contexto ───────────────────────────────────────────────

def _secao(ws, row, texto):
    ws.merge_cells(start_row=row, start_column=1, end_row=row, end_column=5)
    c = ws.cell(row=row, column=1, value="  " + texto)
    c.fill = fill(SLATE); c.font = Font(name=CAL, size=11, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="left", vertical="center")
    ws.row_dimensions[row].height = 20


def _par(ws, row, chave, valor, chave_fill=None):
    a = ws.cell(row=row, column=1, value=chave)
    a.font = Font(name=CAL, size=10, bold=True, color=DARK)
    a.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)
    if chave_fill:
        a.fill = fill(chave_fill)
    ws.merge_cells(start_row=row, start_column=2, end_row=row, end_column=5)
    b = ws.cell(row=row, column=2, value=valor)
    b.fill = fill(ZEBRA); b.font = Font(name=CAL, size=10, color=SLATE)
    b.alignment = Alignment(horizontal="left", vertical="top", wrap_text=True)


def montar_legenda(wb: Workbook) -> None:
    ws = wb.create_sheet("Legenda e Contexto")
    for col, w in {"A": 30, "B": 56, "C": 2, "D": 28, "E": 38}.items():
        ws.column_dimensions[col].width = w

    ws.merge_cells("A1:E1")
    c = ws["A1"]
    c.value = "LEGENDA E CONTEXTO — CRONOGRAMA AUTOMED"
    c.fill = fill(NAVY); c.font = Font(name=CAL, size=14, bold=True, color=WHITE)
    c.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 26

    r = 3
    _secao(ws, r, "STATUS"); r += 1
    for st, txt in [
        ("Não iniciado", "Atividade ainda não começou"),
        ("Em andamento", "Atividade em execução"),
        ("Concluído", "Atividade finalizada e validada"),
        ("Bloqueado", "Aguardando dependência externa"),
        ("Pendente", "Aguardando decisão ou informação"),
    ]:
        _par(ws, r, st, txt, STATUS_FILL[st]); r += 1

    r += 1
    _secao(ws, r, "ESFORÇO"); r += 1
    for e, txt in [("P — Pequeno", "Até 1 dia de trabalho"),
                   ("M — Médio", "2 a 5 dias de trabalho"),
                   ("G — Grande", "Mais de 5 dias de trabalho")]:
        _par(ws, r, e, txt, ESF[e[0]]); r += 1

    r += 1
    _secao(ws, r, "ONDAS (cor da espinha #)"); r += 1
    for n, txt in [
        ("Onda 0 (vermelho)", "Saneamento crítico — GATE: nenhuma ampliação antes de concluí-la"),
        ("Onda 1", "Fundação dos SDKs e cobertura (API + Workers + Frontend Angular)"),
        ("Onda 2", "Contexto de negócio e agrupamento (pipeline de sync + cálculo de produção)"),
        ("Onda 3", "Alertas + Health Checks (API e 3 Workers)"),
        ("Onda 4", "Performance + logs correlacionados (centralizar logs dos Workers)"),
        ("Onda 5", "Métricas de negócio + dashboard por organização/fluxo"),
        ("Onda 6", "Endurecimento, regulatório (ANP) e compliance"),
    ]:
        _par(ws, r, n, txt); r += 1

    r += 1
    _secao(ws, r, "CAMADAS / COMPONENTES"); r += 1
    _par(ws, r, "API",
         "Backend .NET 8 / ASP.NET Core (21 projetos). Projeto Sentry `automed` (dotnet-aspnetcore) — JÁ instalado e "
         "capturando desde 14/04/2026. Controllers por domínio (Auth, Eventos, Entidades, Tarefas...)."); r += 1
    _par(ws, r, "Workers",
         "3 Windows Services .NET: Sync.Worker (orquestra XConnect / PI System / Scan), Tasks.Worker (fila no banco a cada "
         "5s), FileExporter.Worker (diário). Logam no Windows Event Viewer; cobertura Sentry parcial/a confirmar."); r += 1
    _par(ws, r, "Frontend",
         "SPA Angular 13 + PrimeNG. SEM Sentry hoje (nenhum projeto de frontend no org) — cego."); r += 1
    _par(ws, r, "Models / DB",
         "Camada Models (Clean Architecture) compartilhada por API e Workers; SQL Server/Azure SQL, schema por organização, "
         "modelo híbrido relacional+JSON; migrations via EF Core."); r += 2

    _secao(ws, r, "PRINCÍPIO DO PLANO"); r += 1
    _par(ws, r, "Sanear antes de ampliar",
         "A Onda 0 é um gate: corrigir base (environment, release, schema drift/migrações por organização, ruído de host, "
         "reclassificação de domínio, PII) antes de alertas, tracing e métricas. Painel sobre base não saneada é sem sentido."); r += 2

    _secao(ws, r, "BASE DE EVIDÊNCIA (Sentry 01–07/06/2026 + doc + estudo)"); r += 1
    for k, txt in [
        ("Cobertura", "Projeto `automed` (API .NET) instalado desde 14/04. 18 issues, 0 resolvidas. Frontend Angular e Workers (Sync/FileExporter) ainda cegos ou parciais."),
        ("Correção de premissa", "Estudo de abril dizia 'Sentry NÃO instalado em nenhum componente' — na realidade a API JÁ captura. Foco muda para sanear + estender cobertura."),
        ("Schema drift (colunas)", "AceitoUsuario (AUTOMED-Z 185 ev) + KeyNotFound aceitoUsuario (AUTOMED-10 57 ev) + enviado (AUTOMED-Y) — migração EF não aplicada / código à frente do DB."),
        ("Migração por organização", "'Invalid object name <hash>.monitoramentos' (AUTOMED-A 47 + AUTOMED-2 24 ev) — tabela ausente em schema de organização (análogo a migrate_schemas)."),
        ("Ruído de host", "'Cannot determine the https port' (AUTOMED-1, 107 ev) — maior issue único; config de hosting."),
        ("Domínio como error", "UsuarioSendoUtilizado/EventoNaoExistente/UsuarioInvalido + validações (AUTOMED-5 49 ev + G/V/T/B/X/W) capturados como error — reclassificar."),
        ("environment", "Projeto com UM único environment ('production') — QA/HOMOLOG/DEV não isolados."),
        ("Alertas", "Projeto `automed` FORA de qualquer regra de alerta (0 regras próprias)."),
        ("Monitors", "hasMonitors = False — nenhum Cron Monitor para os 3 Workers."),
        ("Tenant", "userCount=1 em todas as issues — contexto de organização/usuário não populado."),
        ("Logs", "Workers logam no Windows Event Viewer, sem agregação central (Automed não tem Loki como o AutoChecker)."),
        ("Regulatório (ANP)", "Arquivo Inválido (AUTOMED-C), BTP já enviado (AUTOMED-X), BSWFiscal já cadastrado (AUTOMED-B) — baixo volume, alto impacto (multa/auditoria)."),
    ]:
        _par(ws, r, k, txt); r += 1

    r += 1
    _secao(ws, r, "FONTES"); r += 1
    for k, txt in [
        ("DOC", "Documentação técnica do Automed (referência produtos-automind + Automed-documentacao.pdf): .NET 8 / Angular 13, 3 Workers, SQL Server, ANP/i-Engine."),
        ("SENTRY", "Snapshot ao vivo do projeto `automed` (org automind-qd), janela 01→07/06/2026 (mesma base do relatório semanal): 18 issues."),
        ("ESTÁTICO", "Oportunidades de Melhoria de Observabilidade - Automed.md (14/04/2026, 12 itens)."),
    ]:
        _par(ws, r, k, txt); r += 1

    r += 1
    _secao(ws, r, "NOTAS"); r += 1
    n_ondas = len(ONDAS)
    n_itens = sum(len(its) for _, _, its in ONDAS)
    for k, txt in [
        ("Total", f"{n_ondas} ondas · {n_itens} itens (Onda 0 = gate de saneamento)."),
        ("Responsáveis", "'A definir' em todas as linhas — equipe do Automed ainda não atribuída por item."),
        ("Semanas", "Relativas (Sem 1..14), sem datas absolutas de calendário — âncora a definir."),
        ("Janela Sentry", "Contagens da janela 01–07/06/2026 (7 dias). Tendência de 30 dias a confirmar no próximo snapshot."),
        ("Aprovação", "Nenhum item deve ser implementado sem revisão e aprovação do time de arquitetura."),
    ]:
        _par(ws, r, k, txt); r += 1


def main() -> None:
    wb = Workbook()
    montar_cronograma(wb)
    montar_legenda(wb)
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    kb = OUTPUT.stat().st_size / 1024
    print(f"OK: {OUTPUT.name} ({kb:.1f} KB)")


if __name__ == "__main__":
    main()
