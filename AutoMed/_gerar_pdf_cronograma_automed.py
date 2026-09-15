# -*- coding: utf-8 -*-
"""Gera o PDF do Cronograma de Observabilidade do AUTOMED.

Lê a mesma estrutura ONDAS do gerador do xlsx (_gerar_xlsx_cronograma_automed.py),
renderiza em HTML estilizado (capa + tabela com ondas coloridas, fills de esforço e
status — mesmo padrão visual do AutoChecker/AutoLoad) e imprime via Edge headless
--print-to-pdf. Sem dependências além da stdlib.

Como rodar:
  python "Cronograma Observabilidade/AutoMed/_gerar_pdf_cronograma_automed.py"
"""
from __future__ import annotations

import importlib.util
import subprocess
import sys
from html import escape
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import pathname2url

ROOT = Path(__file__).resolve().parent
GEN = ROOT / "_gerar_xlsx_cronograma_automed.py"
HTML = ROOT / "Cronograma_Observabilidade_Automed_2026-06-08.html"
PDF = ROOT / "Cronograma_Observabilidade_Automed_2026-06-08.pdf"

EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]

# Importa ONDAS e paletas do gerador do xlsx (fonte única de verdade)
spec = importlib.util.spec_from_file_location("cron_xlsx_automed", GEN)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
ONDAS = mod.ONDAS
ONDA_COR = mod.ONDA_COR
ESF = mod.ESF
STATUS_FILL = mod.STATUS_FILL

ESF_LABEL = {"P": "P", "M": "M", "G": "G"}

CSS = """
@page { size: A4 landscape; margin: 12mm 10mm; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; }
body { font-family: "Red Hat Display", "Segoe UI", system-ui, -apple-system, sans-serif;
       font-size: 8.2pt; line-height: 1.4; color: #1a1726; }
@media screen { body { background: #F3F3F0; } }

/* Barra de topo (só na tela) — marca AutoMind + voltar ao menu */
.topbar { position: sticky; top: 0; z-index: 50; display: flex; align-items: center;
          justify-content: space-between; gap: 16px; padding: 12px 28px;
          background: linear-gradient(180deg,#161420,#100F0F); }
.topbar::after { content:""; position:absolute; left:0; right:0; bottom:0; height:2px;
                 background: linear-gradient(90deg,#FA094E,#03045E); }
.topbar .tb-brand { display:flex; align-items:center; gap:10px; text-decoration:none; }
.topbar .tb-wordmark { font-weight:900; letter-spacing:.20em; font-size:12pt; color:#F3F3F0; }
.topbar .tb-back { font-weight:600; font-size:10.5pt; color:#F3F3F0; text-decoration:none;
                   background:rgba(255,255,255,.08); border:1px solid #332f3d;
                   padding:6px 13px; border-radius:8px; }
.topbar .tb-back:hover { border-color:#FA094E; color:#fff; }

/* Capa */
.cover { height: 180mm; display: flex; flex-direction: column;
         justify-content: center; page-break-after: always; padding: 0 6mm; }
.cover-bar { border-left: 8px solid #44055A; padding: 8px 0 8px 20px; }
.cover-tag { font-size: 11pt; text-transform: uppercase; letter-spacing: 0.18em;
             color: #44055A; font-weight: 700; }
.cover-title { font-size: 30pt; font-weight: 800; line-height: 1.1; margin: 8px 0; color: #100F0F; }
.cover-sub { font-size: 11pt; color: #475569; margin-top: 6px; }
.cover-meta { margin-top: 26px; font-size: 9.5pt; color: #475569; }
.cover-meta b { color: #1a1726; }

h2.section { font-size: 12pt; color: #44055A; border-bottom: 2px solid #e2e8f0;
             padding-bottom: 4px; margin: 16px 0 8px; page-break-after: avoid; }

table { width: 100%; border-collapse: collapse; table-layout: fixed; }
thead th { background: #44055A; color: #fff; font-size: 8pt; font-weight: 700;
           padding: 5px 5px; text-align: left; }
td { padding: 5px 5px; border-bottom: 1px solid #e2e8f0; vertical-align: top;
     word-wrap: break-word; overflow-wrap: anywhere; }
tr { page-break-inside: avoid; }

.wave td { color: #fff; font-weight: 700; font-size: 8.6pt; padding: 6px 8px; }
.num { color: #fff; font-weight: 700; text-align: center; }
.title { font-weight: 700; color: #100F0F; }
.desc { color: #334155; }
.obs { color: #475569; font-size: 7.6pt; font-style: italic; }
.center { text-align: center; }
.chip { display: inline-block; padding: 1px 6px; border-radius: 3px; font-weight: 700; font-size: 7.6pt; }

/* larguras */
col.c-num { width: 3%; } col.c-act { width: 40%; } col.c-cam { width: 9%; }
col.c-esf { width: 4%; } col.c-sem { width: 9%; } col.c-resp { width: 8%; }
col.c-st { width: 9%; } col.c-obs { width: 18%; }

@media print { .topbar { display: none; } }
"""


def chip(text, hexfill, hexfont="1e293b"):
    return f'<span class="chip" style="background:#{hexfill};color:#{hexfont}">{escape(text)}</span>'


def build_html() -> str:
    n_ondas = len(ONDAS)
    n_itens = sum(len(its) for _, _, its in ONDAS)
    rows = []
    rows.append(
        '<table><colgroup>'
        '<col class="c-num"><col class="c-act"><col class="c-cam"><col class="c-esf">'
        '<col class="c-sem"><col class="c-resp"><col class="c-st"><col class="c-obs">'
        '</colgroup><thead><tr>'
        '<th>#</th><th>Onda / Atividade</th><th>Camada</th><th>Esf.</th>'
        '<th>Semanas</th><th>Resp.</th><th>Status</th><th>Observações / Evidência</th>'
        '</tr></thead><tbody>'
    )
    n = 0
    for numero, titulo_barra, itens in ONDAS:
        cor = ONDA_COR[numero]
        rows.append(f'<tr class="wave"><td colspan="8" style="background:#{cor}">{escape(titulo_barra)}</td></tr>')
        for titulo, desc, camada, esf, ini, fim, resp, status, obs in itens:
            n += 1
            sem = ini if ini == fim else f"{ini} – {fim}"
            esf_chip = chip(ESF_LABEL.get(esf, esf), ESF.get(esf, "e2e8f0"))
            st_chip = chip(status, STATUS_FILL.get(status, "e2e8f0"))
            rows.append(
                f'<tr>'
                f'<td class="num" style="background:#{cor}">{n}</td>'
                f'<td><div class="title">{escape(titulo)}</div><div class="desc">{escape(desc)}</div></td>'
                f'<td style="background:#EDE9FE">{escape(camada)}</td>'
                f'<td class="center">{esf_chip}</td>'
                f'<td class="center">{escape(sem)}</td>'
                f'<td class="center">{escape(resp)}</td>'
                f'<td class="center">{st_chip}</td>'
                f'<td class="obs">{escape(obs)}</td>'
                f'</tr>'
            )
    rows.append('</tbody></table>')
    tabela = "\n".join(rows)

    cover = (
        '<div class="cover"><div class="cover-bar">'
        '<div class="cover-tag">Observabilidade · Automind</div>'
        '<div class="cover-title">Cronograma de Observabilidade<br>Automed</div>'
        '<div class="cover-sub">API .NET 8 · 3 Workers (Sync / Tasks / FileExporter) · frontend Angular 13 · SQL Server · ANP / i-Engine</div>'
        '</div>'
        '<div class="cover-meta">'
        '<b>Ferramenta:</b> Sentry (org automind-qd, projeto automed)<br>'
        '<b>Base:</b> doc técnica + snapshot Sentry 01→07/06/2026 (18 issues) + estudo estático 14/04/2026<br>'
        f'<b>Estrutura:</b> {n_ondas} ondas · {n_itens} itens · Onda 0 = gate de saneamento<br>'
        '<b>Nota:</b> o Sentry JÁ captura na API (.NET) desde 14/04 — o plano saneia e estende cobertura (Workers/Frontend)<br>'
        '<b>Data:</b> 08 de junho de 2026'
        '</div></div>'
    )

    topbar = (
        '<div class="topbar">'
        '<a class="tb-brand" href="../../Central/index.html" title="Central de Observabilidade">'
        '<img src="../../Central/am-mark.png" alt="AutoMind" width="30" height="21">'
        '<span class="tb-wordmark">AUTOMIND</span></a>'
        '<a class="tb-back" href="../../Central/index.html">‹ Voltar ao menu</a></div>'
    )

    return (
        f'<!doctype html><html lang="pt-BR"><head><meta charset="utf-8">'
        f'<title>Cronograma de Observabilidade — Automed</title>'
        f'<link rel="preconnect" href="https://fonts.googleapis.com">'
        f'<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>'
        f'<link href="https://fonts.googleapis.com/css2?family=Red+Hat+Display:wght@400;500;600;700;800;900&display=swap" rel="stylesheet">'
        f'<style>{CSS}</style></head><body>'
        f'{topbar}'
        f'{cover}'
        f'<h2 class="section">Cronograma — {n_ondas} ondas, {n_itens} itens</h2>'
        f'{tabela}'
        f'</body></html>'
    )


def find_edge() -> str:
    for c in EDGE_CANDIDATES:
        if Path(c).exists():
            return c
    sys.exit("Edge não encontrado.")


def main() -> None:
    HTML.write_text(build_html(), encoding="utf-8")
    edge = find_edge()
    url = urljoin("file:", pathname2url(str(HTML)))
    if PDF.exists():
        try:
            PDF.unlink()
        except PermissionError:
            sys.exit(f"PDF aberto/bloqueado: feche {PDF.name} e rode de novo.")
    subprocess.run(
        [edge, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={PDF}", url],
        check=True, timeout=120,
    )
    kb = PDF.stat().st_size / 1024
    print(f"OK: {PDF.name} ({kb:.1f} KB)")


if __name__ == "__main__":
    main()
