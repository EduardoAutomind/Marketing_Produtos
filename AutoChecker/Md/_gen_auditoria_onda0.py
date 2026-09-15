# -*- coding: utf-8 -*-
"""Gera o PDF da Auditoria de Conformidade da Onda 0 (AutoChecker x Azure DevOps)."""
import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.platypus import (BaseDocTemplate, PageTemplate, Frame, Paragraph,
                                Spacer, Table, TableStyle, PageBreak, NextPageTemplate)

OUT = r"C:\Projetos\Observabilidade\Cronograma observabilidade\AutoChecker\Auditoria_Onda0_AutoChecker_2026-06-15.pdf"
DATA_HOJE = "15/06/2026"

# ---- cores por classificacao ----
C_OK   = colors.HexColor("#2e7d32")
C_PROG = colors.HexColor("#1565c0")
C_PEND = colors.HexColor("#546e7a")
C_NAO  = colors.HexColor("#c62828")
C_PART = colors.HexColor("#e65100")
C_CONF = colors.HexColor("#f9a825")
INK    = colors.HexColor("#1b2330")
LINE   = colors.HexColor("#c7ced8")
BANDBG = colors.HexColor("#eef2f7")

CLS = {
    "ok":   ("CONCLUIDA",            C_OK),
    "prog": ("EM ANDAMENTO",         C_PROG),
    "pend": ("PLANEJADA / PENDENTE", C_PEND),
    "nao":  ("NAO MAPEADA",          C_NAO),
    "part": ("PARCIAL / AMBIGUA",    C_PART),
    "conf": ("PENDENTE DE CONFIRMACAO", C_CONF),
}

# ---------------- estilos ----------------
ss = getSampleStyleSheet()
def S(name, **kw):
    base = kw.pop("parent", ss["Normal"])
    return ParagraphStyle(name, parent=base, **kw)

st_title   = S("t", parent=ss["Title"], fontSize=26, leading=30, textColor=INK)
st_sub     = S("s", fontSize=13, leading=18, alignment=TA_CENTER, textColor=colors.HexColor("#445"))
st_h1      = S("h1", fontSize=16, leading=20, spaceBefore=6, spaceAfter=10, textColor=INK, fontName="Helvetica-Bold")
st_h2      = S("h2", fontSize=12.5, leading=16, spaceBefore=12, spaceAfter=5, textColor=INK, fontName="Helvetica-Bold")
st_body    = S("b", fontSize=9.7, leading=13.6, textColor=INK, spaceAfter=4, alignment=TA_LEFT)
st_small   = S("sm", fontSize=8.4, leading=11.5, textColor=colors.HexColor("#445"))
st_label   = S("lab", fontSize=9, leading=12, textColor=INK, fontName="Helvetica-Bold")
st_cell    = S("cell", fontSize=8.3, leading=10.8, textColor=INK)
st_cellb   = S("cellb", fontSize=8.3, leading=10.8, textColor=INK, fontName="Helvetica-Bold")
st_cellw   = S("cellw", fontSize=8.3, leading=10.8, textColor=colors.white, fontName="Helvetica-Bold", alignment=TA_CENTER)

def pill(cls):
    txt, col = CLS[cls]
    t = Table([[Paragraph(txt, st_cellw)]], colWidths=[5.2*cm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),col),
                           ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
                           ("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]))
    return t

# ---------------- conteudo: 8 etapas ----------------
# cada etapa: numero, nome, objetivo, achados(lista de linhas), classe, analise, pendencias
ET = [
 (1, "Padronizar tag environment nos 3 SDKs + isolar DEV/PRD",
  "Garantir environment in {production, staging, development} em backend, worker e frontend "
  "(hoje frontend ~15% production, worker ~65%); frontend cai em fallback 'development' quando "
  "NEXT_PUBLIC_SENTRY_ENVIRONMENT nao esta no CI.",
  [("44191","Discovery","Done","Everton L. S. Silva","2025-11-17","Pesquisar metodologia de observabilidade"),
   ("44192","Task","Done","Tarcisio Rocha","2025-11-17","Implementar metodo de observabilidade I"),
   ("44193","Task","Done","Tarcisio Rocha","2025-11-17","Implementar metodo de observabilidade 2/3"),
   ("46787","Task","Done","Tarcisio Rocha","2026-01-26","Implementar metodo de observabilidade II"),
   ("44194","Task","To Do","-","2025-11-17","Implementar metodo de observabilidade 3/3"),
   ("48860","Task","Done","Tarcisio Rocha","2026-03-11","Adicionar o Sentry aos Servicos (back/front/worker/custos OK; scrapping pendente)")],
  "conf",
  "Existem tarefas genericas de 'metodo de observabilidade' (algumas Done) e a inclusao do Sentry "
  "nos servicos (48860). Porem NENHUM work item trata especificamente da padronizacao da tag "
  "environment nem da variavel NEXT_PUBLIC_SENTRY_ENVIRONMENT no CI. Nao e possivel confirmar que o "
  "escopo desta etapa esteja coberto pelas tarefas genericas.",
  "Sem item rastreavel para a tag environment / fallback do frontend. Risco de o frontend continuar "
  "reportando como 'development' em producao."),

 (2, "Padronizar release + set-commits + isolar pipelines Azure",
  "Formato de release <componente>@<hash> nos 3 servicos, ativar set-commits --auto e corrigir os "
  "pipelines Azure; frontend usa org/project de teste (automind-teste / javascript-nextjs) que enviam "
  "source maps para o projeto errado.",
  [("36445","Task","To Do","-","2025-05-22","Configuracao do pipeline de releases no Azure DevOps")],
  "part",
  "O unico work item relacionado (36445) trata genericamente de 'pipeline de releases', esta em 'To Do' "
  "desde mai/2025 e sem responsavel. Nao ha item algum para set-commits, source maps ou correcao de "
  "org/project do Sentry. Observacao tecnica (fora do Azure Boards): a inspecao ao vivo dos pipelines "
  "mostrou release backend@/worker@ ja implementado via deploy SSH, mas isso NAO esta refletido em "
  "nenhum work item.",
  "Escopo da etapa coberto so de forma parcial e nao iniciada nos Boards. set-commits e org/project do "
  "frontend totalmente nao mapeados."),

 (3, "Limpar PeriodicTask orfa do Beat (KeyError process_scheduled_notifications)",
  "Remover/migrar a entrada orfa process_scheduled_notifications do django-celery-beat (gera ~1.541 "
  "KeyError por dispatch) e alinhar o schedule do DB com o codigo.",
  [("53659","Bug","Done","Tarcisio Rocha","2026-05-18","Limpar beat_schedule do backend e resetar celerybeat-schedule em prod"),
   ("40384","Task","Done","Tarcisio Rocha","2025-09-02","Ajustar tasks do Celery BEAT"),
   ("53660","Task","To Do","Tarcisio Rocha","2026-05-18","Limpar beat_schedule (Task duplicada da 53659, aberta)"),
   ("53707","Task","To Do","-","2026-05-19","Limpeza preventiva do celerybeat-schedule no deploy (continuacao de 53659)")],
  "part",
  "O nucleo do problema foi tratado: a Bug 53659 (Done) limpou o beat_schedule e resetou o "
  "celerybeat-schedule em prod. Porem NENHUM item nomeia a task orfa 'process_scheduled_notifications' "
  "explicitamente, a Task-par 53660 ficou 'To Do' (duplicidade nao reconciliada) e a continuacao 53707 "
  "(integrar a limpeza ao ciclo de deploy) segue 'To Do'.",
  "Falta a etapa preventiva no deploy (53707) e reconciliar a duplicata 53660. Sem isso, a entrada orfa "
  "pode voltar em novos deploys."),

 (4, "Corrigir migracoes faltando em schemas de tenant (migrate_schemas)",
  "Deploy roda apenas migrate / migrate --plan, nunca migrate_schemas, causando ~57 issues "
  "'relation ... does not exist'. Adicionar migrate_schemas ao processo de deploy.",
  [("51820","Task","To Do","Tarcisio Rocha","2026-05-04","relation 'upload_document' does not exist (issue Sentry)"),
   ("35848","Task","To Do","-","2025-05-12","Testes de migracao de schema em multiplos tenants"),
   ("35829","Task","Removed","Antonio M. B. Souza","2025-05-12","Estrategia para migracoes de schemas de tenants (REMOVIDA)")],
  "part",
  "Ha um sintoma exato registrado (51820, 'relation does not exist', em 'To Do') e tarefas antigas de "
  "estrategia/teste de migracao de schema (35829 Removida, 35848 To Do de 2025). Mas NAO existe work "
  "item para a correcao sistemica pedida pela etapa: adicionar 'migrate_schemas' ao deploy. As mencoes "
  "a migrate_schemas em 47359/47542 sao de outro contexto (unificacao de autenticacao).",
  "A causa-raiz (deploy sem migrate_schemas) nao tem item. Apenas sintomas isolados foram ticketados."),

 (5, "Consolidar init no helper init_sentry + ativar CeleryIntegration no backend",
  "Backend e worker fazem sentry_sdk.init() de forma divergente; backend so tem DjangoIntegration e "
  "RedisIntegration, sem CeleryIntegration. Consolidar ambos no helper init_sentry.",
  [],
  "nao",
  "Busca por 'init_sentry' e 'CeleryIntegration' (titulo e descricao) retornou ZERO work items. A unica "
  "tarefa proxima (48860, Done) trata de 'adicionar o Sentry aos servicos', nao da consolidacao do "
  "helper de init nem da CeleryIntegration. Nenhuma evidencia rastreavel.",
  "Etapa totalmente nao mapeada. Sem CeleryIntegration, erros de tasks Celery podem nao ser capturados/"
  "agrupados corretamente."),

 (6, "before_send / Inbound Filters: remover ruido de scanner, auth e health endpoint morto",
  "Filtrar DisallowedHost (127 ev), JWT/SchemaHeader (275 ev) e corrigir o filtro morto que tenta "
  "filtrar /health/ quando o endpoint real e /api/core/healthcheck/.",
  [("53661","Bug","Done","Tarcisio Rocha","2026-05-18","Validar UUID no _set_tenant_by_id do SchemaHeaderMiddleware"),
   ("53662","Task","To Do","Tarcisio Rocha","2026-05-18","Validar UUID no SchemaHeaderMiddleware (Task-par, aberta)"),
   ("53706","Task","To Do","-","2026-05-19","Middleware: retornar 400 em rotas TENANT_APP sem header de tenant"),
   ("53684","PBI","New","-","2026-05-18","[Infra] Implementar health check endpoint e monitoramento proativo"),
   ("53997","Task","To Do","-","2026-05-20","[Infra] Criar endpoint /healthcheck/detailed/")],
  "part",
  "Parte do ruido de SchemaHeader foi atacada na origem (53661 Done valida UUID no middleware), o que "
  "reduz parte dos 275 eventos. Mas NAO ha item para configurar before_send / Inbound Filters, nem para "
  "DisallowedHost, nem para corrigir o filtro morto /health/ vs /api/core/healthcheck/. Os itens de "
  "healthcheck (53684/53997) criam endpoints novos, nao corrigem o filtro do Sentry.",
  "before_send, DisallowedHost e o filtro de health morto seguem nao mapeados; o ruido dominante no "
  "Sentry nao sera eliminado so com 53661."),

 (7, "Scrubbing de PII/LGPD no Frontend + Data Scrubber",
  "Frontend com sendDefaultPii: true nos 3 configs + Sentry.setUser({email}) + Session Replay sem "
  "masking sobre telas de CNH/ASO/CPF. Corrigir exposicao de dados pessoais.",
  [("55050","Feature","New","Gabriel S. B. Santos","2026-06-09","Aceite Digital de Termos e Politica de Privacidade (LGPD) - PRODUTO"),
   ("55088","PBI","New","Gabriel S. B. Santos","2026-06-10","Central de Ajuda autenticada (Portal LGPD do titular) - PRODUTO")],
  "nao",
  "Busca por 'sendDefaultPii', 'scrubbing', 'data scrubber' e 'PII' (titulo/descricao) nao retornou "
  "nenhum item ligado ao Sentry. Os itens de LGPD encontrados (55050, 55088) sao de PRODUTO (aceite de "
  "termos, central de ajuda) e nao tratam de mascarar PII no Sentry / Session Replay. Etapa nao mapeada.",
  "Exposicao de PII no Sentry (email do usuario, Session Replay sem masking de CNH/ASO/CPF) sem nenhum "
  "item de correcao. RISCO LEGAL/LGPD relevante."),

 (8, "Triagem ZERO do backlog (152 issues abertas no Sentry)",
  "0 issues resolvidas em 30 dias. Realizar triagem completa do backlog, classificando como Resolvido, "
  "Ignorado, Em andamento ou Aguardando.",
  [("53700","Bug","New","-","2026-05-19","Estabilizacao de Issues Sentry - Maio/2026 (guarda-chuva, 7 filhos)"),
   ("51817","Bug","New","Tarcisio Rocha","2026-05-04","Sentry Erros (guarda-chuva, 4 filhos)"),
   ("51818","Task","Done","Tarcisio Rocha","2026-05-04","Sentry - EnsureUserAndLogin duplicate key (resolvido)"),
   ("53701-53707","Task","To Do","varios","2026-05-19","7 filhos de 53700 (maioria To Do)")],
  "prog",
  "Existe esforco de triagem ATIVO: dois guarda-chuvas (53700 'Estabilizacao de Issues Sentry' e 51817 "
  "'Sentry Erros') com filhos derivados de issues reais do Sentry. Porem ambos os guarda-chuvas estao "
  "'New', poucos filhos estao Done (ex.: 51818) e a maioria segue 'To Do'. Nao e uma triagem completa "
  "fechada do backlog de 152 issues - e uma triagem parcial e reativa.",
  "A triagem nao esta concluida; o backlog completo nao foi classificado. Guarda-chuvas abertos."),
]

# ---------------- documento ----------------
PAGE_W, PAGE_H = A4
def footer(canvas, doc):
    canvas.saveState()
    canvas.setStrokeColor(LINE); canvas.setLineWidth(0.5)
    canvas.line(2*cm, 1.4*cm, PAGE_W-2*cm, 1.4*cm)
    canvas.setFont("Helvetica", 7.5); canvas.setFillColor(colors.HexColor("#667"))
    canvas.drawString(2*cm, 1.0*cm, "Automind - Relatorio de Auditoria de Observabilidade - AutoChecker Onda 0")
    canvas.drawRightString(PAGE_W-2*cm, 1.0*cm, "Pagina %d" % doc.page)
    canvas.restoreState()

def cover(canvas, doc):
    canvas.saveState()
    canvas.setFillColor(INK); canvas.rect(0, PAGE_H-3.2*cm, PAGE_W, 3.2*cm, fill=1, stroke=0)
    canvas.setFillColor(colors.HexColor("#6ea8fe"))
    canvas.rect(0, PAGE_H-3.35*cm, PAGE_W, 0.15*cm, fill=1, stroke=0)
    footer(canvas, doc)
    canvas.restoreState()

frame = Frame(2*cm, 1.7*cm, PAGE_W-4*cm, PAGE_H-3.4*cm, id="main")
frame_cover = Frame(2*cm, 1.7*cm, PAGE_W-4*cm, PAGE_H-6.5*cm, id="cover")
doc = BaseDocTemplate(OUT, pagesize=A4, title="Auditoria de Conformidade - Onda 0",
                      author="Automind", leftMargin=2*cm, rightMargin=2*cm)
doc.addPageTemplates([
    PageTemplate(id="cover", frames=[frame_cover], onPage=cover),
    PageTemplate(id="body",  frames=[frame],       onPage=footer),
])

story = []
# ---- CAPA ----
story += [Spacer(1, 3.2*cm)]
story += [Paragraph("Auditoria de Conformidade", st_title)]
story += [Paragraph("Onda 0 - Saneamento da Base", S("c2", fontSize=18, leading=22, textColor=C_NAO, fontName="Helvetica-Bold"))]
story += [Spacer(1, 0.5*cm)]
story += [Paragraph("Cronograma de Observabilidade AutoChecker &times; Azure DevOps", st_sub)]
story += [Spacer(1, 1.6*cm)]
meta = Table([
    [Paragraph("Data de geracao", st_label), Paragraph(DATA_HOJE, st_body)],
    [Paragraph("Produto", st_label), Paragraph("AutoChecker", st_body)],
    [Paragraph("Ferramenta", st_label), Paragraph("Sentry (org: automind-qd)", st_body)],
    [Paragraph("Fonte de verdade", st_label), Paragraph("Azure DevOps - org automindautomacao / projeto AutoChecker (work items via REST API)", st_body)],
    [Paragraph("Escopo", st_label), Paragraph("8 etapas (itens 1 a 8 do cronograma)", st_body)],
], colWidths=[4*cm, PAGE_W-4*cm-4*cm])
meta.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,-2),0.4,LINE),("VALIGN",(0,0),(-1,-1),"TOP"),
                          ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6)]))
story += [meta]
story += [Spacer(1, 1.2*cm)]
story += [Paragraph("<b>Veredito-resumo:</b> a Onda 0 NAO esta apta a ser considerada concluida. "
                    "Nenhuma das 8 etapas possui work item em estado 'Done' cujo escopo cubra a etapa. "
                    "O gate deve permanecer FECHADO.", S("verd", fontSize=10.5, leading=15, textColor=INK,
                    backColor=colors.HexColor("#fdecea"), borderColor=C_NAO, borderWidth=1, borderPadding=8))]

story += [NextPageTemplate("body"), PageBreak()]

# ---- SECAO 1 ----
story += [Paragraph("1. Introducao", st_h1)]
story += [Paragraph("<b>O que e a Onda 0.</b> A Onda 0 (Saneamento da Base) e o primeiro bloco do "
   "cronograma de observabilidade do AutoChecker e funciona como um <b>gate obrigatorio</b>: enquanto "
   "ela nao estiver concluida, as ondas seguintes (1 a 6) nao devem avancar. Ela concentra a correcao "
   "de configuracoes de ambiente/release no Sentry, a eliminacao do ruido dominante e a triagem do "
   "backlog de issues.", st_body)]
story += [Paragraph("<b>Escopo da auditoria.</b> Foram auditadas as 8 etapas (itens 1 a 8). Para cada "
   "uma, buscou-se no Azure DevOps por work items (Task, Bug, PBI, Feature) correspondentes, "
   "registrando ID, titulo, estado, responsavel e datas.", st_body)]
story += [Paragraph("<b>Fontes de dados.</b> A unica fonte de verdade desta auditoria e o Azure DevOps "
   "(org automindautomacao, projeto AutoChecker), consultado via REST API/WIQL em 15/06/2026 (2.133 "
   "work items no projeto). O texto do cronograma foi usado apenas como referencia do escopo esperado "
   "de cada etapa. Nao foram usadas suposicoes nem inferencias: onde nao houve item, registra-se "
   "'Nao mapeada'.", st_body)]
story += [Paragraph("<b>Metodo de classificacao.</b> Buscas por titulo (CONTAINS) e por descricao "
   "(CONTAINS WORDS) com os termos tecnicos de cada etapa, mais a expansao das features guarda-chuva "
   "de observabilidade (40531) e de estabilizacao do Sentry (53700, 51817) e seus filhos.", st_body)]

# legenda de classificacoes
story += [Spacer(1,0.2*cm), Paragraph("Legenda das classificacoes", st_h2)]
leg_rows = [[Paragraph("Classificacao", st_cellb), Paragraph("Quando se aplica", st_cellb)]]
leg_map = [("ok","Work item 'Done/Closed' e escopo bate com a etapa"),
           ("prog","Work item 'Active/In Progress/Em andamento'"),
           ("pend","Work item criado mas nao iniciado (To Do/New/Backlog)"),
           ("nao","Nenhum work item encontrado para a etapa"),
           ("part","Existe item, mas o escopo nao cobre tudo ou o estado e ambiguo"),
           ("conf","Item encontrado, mas nao da para confirmar que se refere a esta etapa")]
for k,desc in leg_map:
    leg_rows.append([Paragraph(CLS[k][0], S("lg",fontSize=8.3,leading=10.5,textColor=colors.white,fontName="Helvetica-Bold")),
                     Paragraph(desc, st_cell)])
legt = Table(leg_rows, colWidths=[5.2*cm, PAGE_W-4*cm-5.2*cm])
sty=[("GRID",(0,0),(-1,-1),0.4,LINE),("VALIGN",(0,0),(-1,-1),"MIDDLE"),
     ("BACKGROUND",(0,0),(-1,0),BANDBG),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]
for i,(k,_) in enumerate(leg_map, start=1):
    sty.append(("BACKGROUND",(0,i),(0,i),CLS[k][1]))
legt.setStyle(TableStyle(sty))
story += [legt]

story += [PageBreak()]

# ---- SECAO 2 ----
story += [Paragraph("2. Analise por Etapa", st_h1)]
for (num,nome,obj,achados,cls,analise,pend) in ET:
    story += [Paragraph("Etapa %d - %s" % (num, nome), st_h2)]
    story += [pill(cls), Spacer(1,0.15*cm)]
    story += [Paragraph("<b>Objetivo do cronograma.</b> " + obj, st_body)]
    story += [Paragraph("<b>Encontrado no Azure DevOps.</b>", st_body)]
    if achados:
        rows = [[Paragraph("ID", st_cellb),Paragraph("Tipo", st_cellb),Paragraph("Estado", st_cellb),
                 Paragraph("Responsavel", st_cellb),Paragraph("Criado", st_cellb),Paragraph("Titulo", st_cellb)]]
        for (wid,typ,est,resp,dt,tit) in achados:
            estyle = st_cell
            rows.append([Paragraph(wid,st_cell),Paragraph(typ,st_cell),Paragraph(est,st_cellb),
                         Paragraph(resp,st_cell),Paragraph(dt,st_cell),Paragraph(tit,st_cell)])
        t = Table(rows, colWidths=[1.6*cm,1.4*cm,1.5*cm,2.7*cm,1.7*cm,PAGE_W-4*cm-8.9*cm])
        tsty=[("GRID",(0,0),(-1,-1),0.4,LINE),("BACKGROUND",(0,0),(-1,0),BANDBG),
              ("VALIGN",(0,0),(-1,-1),"TOP"),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3)]
        # colorir estado
        for ri,(wid,typ,est,resp,dt,tit) in enumerate(achados, start=1):
            ce = C_OK if est=="Done" else (C_NAO if est in ("To Do","New","Removed") else C_PROG)
            tsty.append(("TEXTCOLOR",(2,ri),(2,ri),ce))
        t.setStyle(TableStyle(tsty))
        story += [t]
    else:
        story += [Paragraph("[Nao encontrado no Azure DevOps] - nenhum work item para os termos da etapa.",
                            S("ne", fontSize=9, leading=12, textColor=C_NAO, fontName="Helvetica-Bold"))]
    story += [Spacer(1,0.1*cm)]
    story += [Paragraph("<b>Analise.</b> " + analise, st_body)]
    story += [Paragraph("<b>Pendencias / Riscos.</b> " + pend, st_body)]
    story += [Spacer(1,0.35*cm)]

story += [PageBreak()]

# ---- SECAO 3 ----
story += [Paragraph("3. Resumo Executivo", st_h1)]
story += [Paragraph("Tabela de status geral da Onda 0", st_h2)]
hdr = [Paragraph(x, st_cellw if False else st_cellb) for x in ["#","Etapa","Classificacao","Responsavel (Azure)","Risco"]]
sum_rows = [hdr]
SUMMARY = [
 (1,"Tag environment + isolar DEV/PRD","conf","Tarcisio Rocha (genericos)","Frontend pode reportar como 'development' em prod"),
 (2,"Release + set-commits + pipelines","part","- (36445 sem dono)","set-commits/source maps/org errado nao mapeados"),
 (3,"PeriodicTask orfa do Beat","part","Tarcisio Rocha","Prevencao no deploy aberta; orfa pode voltar"),
 (4,"migrate_schemas no deploy","part","Tarcisio Rocha (sintoma)","Causa-raiz das ~57 issues sem item"),
 (5,"init_sentry + CeleryIntegration","nao","-","Erros de Celery podem nao ser capturados"),
 (6,"before_send / Inbound Filters","part","Tarcisio Rocha (parcial)","Ruido dominante (scanner/health) segue"),
 (7,"Scrubbing PII/LGPD no Frontend","nao","-","RISCO LEGAL: PII exposta no Sentry/Replay"),
 (8,"Triagem ZERO do backlog","prog","Tarcisio Rocha","Triagem parcial; backlog nao fechado"),
]
for (n,et,cls,resp,risco) in SUMMARY:
    sum_rows.append([Paragraph(str(n),st_cell),Paragraph(et,st_cell),
                     Paragraph(CLS[cls][0],S("sc",fontSize=7.6,leading=9.6,textColor=colors.white,fontName="Helvetica-Bold")),
                     Paragraph(resp,st_cell),Paragraph(risco,st_cell)])
sumt = Table(sum_rows, colWidths=[0.8*cm,4.6*cm,3.5*cm,3.3*cm,PAGE_W-4*cm-12.2*cm])
ssty=[("GRID",(0,0),(-1,-1),0.4,LINE),("BACKGROUND",(0,0),(-1,0),BANDBG),
      ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4)]
for i,(n,et,cls,resp,risco) in enumerate(SUMMARY, start=1):
    ssty.append(("BACKGROUND",(2,i),(2,i),CLS[cls][1]))
sumt.setStyle(TableStyle(ssty))
story += [sumt, Spacer(1,0.4*cm)]

story += [Paragraph("Contagem por classificacao", st_h2)]
cnt_rows = [[Paragraph("Concluidas",st_cellb),Paragraph("Em andamento",st_cellb),Paragraph("Planejadas/Pendentes",st_cellb),
             Paragraph("Nao mapeadas",st_cellb),Paragraph("Parciais/Ambiguas",st_cellb),Paragraph("Pend. confirmacao",st_cellb)],
            [Paragraph("0",st_cellb),Paragraph("1",st_cellb),Paragraph("0",st_cellb),
             Paragraph("2",st_cellb),Paragraph("4",st_cellb),Paragraph("1",st_cellb)]]
cw = (PAGE_W-4*cm)/6
cntt = Table(cnt_rows, colWidths=[cw]*6)
cntt.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.4,LINE),("ALIGN",(0,0),(-1,-1),"CENTER"),
    ("VALIGN",(0,0),(-1,-1),"MIDDLE"),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
    ("BACKGROUND",(0,0),(0,1),C_OK),("BACKGROUND",(1,0),(1,1),C_PROG),("BACKGROUND",(2,0),(2,1),C_PEND),
    ("BACKGROUND",(3,0),(3,1),C_NAO),("BACKGROUND",(4,0),(4,1),C_PART),("BACKGROUND",(5,0),(5,1),C_CONF),
    ("TEXTCOLOR",(0,0),(-1,-1),colors.white)]))
story += [cntt, Spacer(1,0.4*cm)]

story += [Paragraph("Diagnostico geral", st_h2)]
story += [Paragraph("<b>A Onda 0 esta apta a ser considerada concluida?</b> NAO. Zero etapas com work "
   "item 'Done' cobrindo o escopo. 4 estao parciais/ambiguas, 2 sem nenhum mapeamento, 1 pendente de "
   "confirmacao e 1 em andamento.", st_body)]
story += [Paragraph("<b>Etapas bloqueadoras para avancar para a Onda 1.</b> Todas as 8, por ausencia de "
   "evidencia de conclusao. As mais criticas sao a Etapa 5 (init_sentry/CeleryIntegration - sem item) e "
   "a Etapa 7 (PII/LGPD - sem item e com risco legal), alem da Etapa 6 (ruido dominante nao eliminado) "
   "e da Etapa 8 (triagem nao fechada).", st_body)]
story += [Paragraph("<b>Risco de avancar sem concluir a Onda 0.</b> Alto. Sem saneamento, as ondas "
   "seguintes seriam construidas sobre dados de Sentry poluidos (ruido de scanner/auth/health), ambiente "
   "mal classificado, releases sem rastreabilidade de commit e exposicao de PII - comprometendo metricas, "
   "alertas e conformidade LGPD.", st_body)]

story += [Paragraph("Recomendacoes prioritarias", st_h2)]
story += [Paragraph("<b>1. Criar work items rastreaveis para as 8 etapas.</b> Hoje as etapas da Onda 0 "
   "nao existem como itens dedicados no Azure Boards - a auditoria nao pode ser fechada por falta de "
   "rastreabilidade. Quebrar a Feature 40531 (Observabilidade) em 8 itens, um por etapa.", st_body)]
story += [Paragraph("<b>2. Tratar com urgencia a Etapa 7 (PII/LGPD no Sentry).</b> Risco legal, zero "
   "mapeamento: desativar sendDefaultPii, remover email do setUser e aplicar masking no Session Replay "
   "sobre telas de CNH/ASO/CPF.", st_body)]
story += [Paragraph("<b>3. Reconciliar os pares Bug(Done)+Task(To Do) duplicados e fechar a triagem.</b> "
   "Pares como 53659/53660 e 53661/53662 deixam o estado real ambiguo; os guarda-chuvas de triagem "
   "(53700, 51817) seguem 'New'. Alinhar os estados para que o Boards reflita a realidade.", st_body)]

doc.build(story)
print("PDF gerado em:", OUT)
print("Existe:", os.path.exists(OUT), "| bytes:", os.path.getsize(OUT) if os.path.exists(OUT) else 0)
