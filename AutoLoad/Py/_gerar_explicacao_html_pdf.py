# -*- coding: utf-8 -*-
"""Gera o HTML (estilo dark do AutoChecker) e o PDF da Explicacao da Onda 0 do AutoLoad V4
a partir de Md/Explicacao_Onda0_AutoLoad_V4_2026-06-17.md.
Reaproveita o CSS de Html/_css_ref.css (extraido da explicacao do AutoChecker).
Imprime o PDF via Edge/Chrome headless --print-to-pdf."""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import pathname2url
import markdown as md_lib

CSS = r"""
  :root{
    --bg:#1e2230;            /* dark, mas não tão escuro */
    --bg-soft:#272c3d;
    --bg-card:#2b3146;
    --border:#3a4159;
    --text:#e6e9f2;
    --text-soft:#b8bfd4;
    --muted:#8a92ad;
    --accent:#7aa2ff;
    --accent-soft:#9db8ff;
    --green:#5cd6a0;
    --yellow:#f2c94c;
    --red:#ff7b7b;
    --blue:#69b7ff;
    --code-bg:#1a1e2b;
    --code-text:#ffd9a8;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{
    margin:0;
    background:var(--bg);
    color:var(--text);
    font-family:"Segoe UI",system-ui,-apple-system,Roboto,Helvetica,Arial,sans-serif;
    line-height:1.65;
    font-size:16px;
  }
  .wrap{max-width:920px;margin:0 auto;padding:48px 28px 80px;}
  h1{
    font-size:2rem;line-height:1.25;margin:0 0 8px;
    color:#fff;font-weight:700;letter-spacing:-.01em;
  }
  h2{
    font-size:1.45rem;margin:48px 0 14px;padding-top:18px;
    border-top:1px solid var(--border);color:#fff;font-weight:650;
  }
  h2:first-of-type{border-top:none;}
  h3{font-size:1.05rem;margin:20px 0 6px;color:var(--accent-soft);font-weight:600;}
  p{margin:10px 0;color:var(--text-soft);}
  strong{color:var(--text);font-weight:650;}
  a{color:var(--accent);}
  code{
    background:var(--code-bg);color:var(--code-text);
    padding:.12em .4em;border-radius:5px;font-size:.86em;
    font-family:"Cascadia Code",Consolas,"Courier New",monospace;
  }
  ul{margin:10px 0;padding-left:22px;}
  li{margin:6px 0;color:var(--text-soft);}
  /* intro box */
  .intro{
    background:var(--bg-soft);border:1px solid var(--border);
    border-left:4px solid var(--accent);border-radius:10px;
    padding:18px 22px;margin:20px 0 8px;
  }
  .intro p{margin:6px 0;color:var(--text-soft);}
  .meta-table{width:100%;border-collapse:collapse;margin-top:10px;}
  .meta-table td{padding:4px 10px 4px 0;vertical-align:top;border:none;color:var(--text-soft);}
  .meta-table td:first-child{color:var(--muted);white-space:nowrap;width:200px;}
  /* etapa card */
  .etapa{
    background:var(--bg-card);border:1px solid var(--border);
    border-radius:12px;padding:6px 26px 22px;margin:18px 0;
  }
  /* tables */
  table{width:100%;border-collapse:collapse;margin:18px 0;font-size:.92rem;}
  th,td{border:1px solid var(--border);padding:9px 12px;text-align:left;vertical-align:top;}
  th{background:var(--bg-soft);color:#fff;font-weight:600;}
  tbody tr:nth-child(even){background:rgba(255,255,255,.02);}
  /* status badges */
  .badge{display:inline-block;padding:.12em .55em;border-radius:20px;font-size:.82em;font-weight:600;white-space:nowrap;}
  .b-done{background:rgba(92,214,160,.16);color:var(--green);}
  .b-prog{background:rgba(105,183,255,.16);color:var(--blue);}
  .b-warn{background:rgba(242,201,76,.16);color:var(--yellow);}
  .b-none{background:rgba(255,123,123,.16);color:var(--red);}
  .b-conf{background:rgba(154,184,255,.16);color:var(--accent-soft);}
  /* callouts */
  .callout{
    border-radius:10px;padding:14px 18px;margin:18px 0;
    border-left:4px solid var(--accent);background:var(--bg-soft);
  }
  .callout.danger{border-left-color:var(--red);background:rgba(255,123,123,.07);}
  .callout.warn{border-left-color:var(--yellow);background:rgba(242,201,76,.07);}
  .callout p{margin:4px 0;}
  blockquote{
    margin:18px 0;padding:12px 18px;border-left:4px solid var(--accent);
    background:var(--bg-soft);border-radius:0 8px 8px 0;color:var(--text-soft);
  }
  .verdict{
    font-size:1.12rem;font-weight:650;color:#fff;
    background:rgba(255,123,123,.1);border:1px solid rgba(255,123,123,.35);
    border-radius:10px;padding:16px 20px;margin:18px 0;
  }
  hr{border:none;border-top:1px solid var(--border);margin:34px 0;}
  .footer{margin-top:40px;font-size:.82rem;color:var(--muted);font-style:italic;border-top:1px solid var(--border);padding-top:18px;}
  .section-label{color:var(--green);font-weight:600;}
"""

ROOT = Path(__file__).resolve().parent.parent
MD   = ROOT / "Md"   / "Explicacao_Onda0_AutoLoad_V4_2026-06-17.md"
HTML = ROOT / "Html" / "Explicacao_Onda0_AutoLoad_V4_2026-06-17.html"
PDF  = ROOT / "Pdf"  / "Explicacao_Onda0_AutoLoad_V4_2026-06-17.pdf"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

# emoji do status -> classe de badge (mesmas cores do AutoChecker)
BADGE = {
    "⚠️": ("b-warn", "Divergente"),
    "🟦": ("b-done", "Improcedente / já concluído"),
    "❓": ("b-conf", "Não verificável no código"),
    "✅": ("b-done", "Conforme"),
    "❌": ("b-none", "Faltando"),
    "🔄": ("b-prog", "Em andamento"),
}

def mdi(text: str) -> str:
    h = md_lib.markdown(text.strip(), extensions=["tables", "sane_lists"]).strip()
    m = re.fullmatch(r"<p>(.*)</p>", h, flags=re.S)
    return m.group(1).strip() if m else h

def md(text: str) -> str:
    return md_lib.markdown(text.strip(), extensions=["tables", "sane_lists"])

def badge_status(html_block: str) -> str:
    """Acha o emoji de status no comeco do bloco e o troca por um <span class=badge>."""
    for emo, (cls, _lbl) in BADGE.items():
        if emo in html_block:
            # captura "EMOJI **Rotulo.**" no inicio do paragrafo
            m = re.search(re.escape(emo) + r"\s*<strong>(.*?)</strong>", html_block)
            if m:
                rot = m.group(1).rstrip(".")
                span = f'<span class="badge {cls}">{emo} {rot}</span>'
                return html_block[:m.start()] + span + html_block[m.end():]
            # fallback: so o emoji
            return html_block.replace(emo, f'<span class="badge {cls}">{emo}</span>', 1)
    return html_block

def build():
    raw = MD.read_text(encoding="utf-8")
    css = CSS

    # separa em blocos por heading de nivel 1/2
    heads = list(re.finditer(r"(?m)^(#{1,2})\s+(.*)$", raw))
    out = []
    title_doc = "Explicação da Onda 0 — AutoLoad V4"

    i = 0
    while i < len(heads):
        h = heads[i]
        level = len(h.group(1))
        title = h.group(2).strip()
        start = h.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(raw)
        body = raw[start:end]
        # remove separadores ---
        body_clean = re.sub(r"(?m)^\s*---\s*$", "", body).strip()

        if level == 1:
            # H1 = titulo do documento + bloco intro (a blockquote inicial)
            mbq = re.search(r"(?m)^(>.*(?:\n>.*)*)", body)
            intro_md = ""
            if mbq:
                intro_md = re.sub(r"(?m)^>\s?", "", mbq.group(1))
            out.append(f'<h1>{mdi(title)}</h1>')
            if intro_md:
                # separa o paragrafo "Para quem..." da tabela (1a linha iniciando com '|')
                lines = intro_md.splitlines()
                tbl_i = next((n for n, ln in enumerate(lines) if ln.lstrip().startswith("|")), len(lines))
                lead = mdi("\n".join(lines[:tbl_i]).strip())
                table_md = "\n".join(lines[tbl_i:]).strip()
                table_html = md(table_md) if table_md else ""
                # converte a tabela do markdown numa meta-table sem cabecalho
                table_html = table_html.replace("<table>", '<table class="meta-table">')
                # remove o <thead> vazio gerado pela linha "| | |"
                table_html = re.sub(r"<thead>.*?</thead>", "", table_html, flags=re.S)
                out.append('<div class="intro"><p>' + lead + '</p>' + table_html + '</div>')
            i += 1
            continue

        # level == 2
        t = title
        if t.startswith("Etapa"):
            card = ['<div class="etapa">', f'<h2>{mdi(t)}</h2>']
            # quebra por ### subtitulos
            subs = list(re.finditer(r"(?m)^###\s+(.*)$", body_clean))
            for k, s in enumerate(subs):
                sub_t = s.group(1).strip()
                s_start = s.end()
                s_end = subs[k + 1].start() if k + 1 < len(subs) else len(body_clean)
                sub_body = body_clean[s_start:s_end].strip()
                block = md(sub_body)
                if "Status segundo" in sub_t:
                    block = badge_status(block)
                card.append(f'<h3>{mdi(sub_t)}</h3>')
                card.append(block)
            card.append('</div>')
            out.append("\n".join(card))
        elif t.startswith("Conclusão"):
            # destaca a primeira frase em negrito como .verdict
            block = md(body_clean)
            mver = re.search(r"<p>(<strong>.*?</strong>.*?)</p>", block, re.S)
            if mver:
                verdict = mver.group(1)
                block = block[:mver.start()] + f'<div class="verdict">{verdict}</div>' + block[mver.end():]
            # "Recomendação" vira callout
            block = re.sub(r"<p>(<strong>Recomendação:</strong>.*?)</p>",
                           r'<div class="callout warn"><p>\1</p></div>', block, flags=re.S)
            out.append('<h2>Conclusão</h2>' + block)
        elif t.startswith("Resumo geral"):
            out.append(f'<h2>{mdi(t)}</h2>' + md(body_clean))
        else:
            out.append(f'<h2>{mdi(t)}</h2>' + md(body_clean))
        i += 1

    body_html = "\n\n".join(out)
    # callouts de blockquote no corpo (a nota "Uma diferenca importante")
    body_html = re.sub(
        r"<blockquote>\s*<p>(.*?)</p>\s*</blockquote>",
        r'<div class="callout"><p>\1</p></div>', body_html, flags=re.S)

    html = (
        '<!DOCTYPE html>\n<html lang="pt-BR">\n<head>\n'
        '<meta charset="UTF-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
        f'<title>{title_doc}</title>\n'
        f'<style>{css}</style>\n</head>\n<body>\n<div class="wrap">\n\n'
        + body_html +
        '\n\n</div>\n</body>\n</html>\n'
    )
    HTML.write_text(html, encoding="utf-8")
    print(f"HTML: {HTML.name} ({HTML.stat().st_size/1024:.1f} KB)")

def to_pdf():
    browser = next((c for c in BROWSERS if Path(c).exists()), None)
    if not browser:
        sys.exit("Nenhum navegador (Edge/Chrome) encontrado para gerar o PDF.")
    url = urljoin("file:", pathname2url(str(HTML)))
    if PDF.exists():
        try:
            PDF.unlink()
        except PermissionError:
            sys.exit(f"PDF aberto/bloqueado: feche {PDF.name} e rode de novo.")
    subprocess.run(
        [browser, "--headless", "--disable-gpu", "--no-pdf-header-footer",
         f"--print-to-pdf={PDF}", url],
        check=True, timeout=180,
    )
    print(f"PDF:  {PDF.name} ({PDF.stat().st_size/1024:.1f} KB)  via {Path(browser).name}")

if __name__ == "__main__":
    build()
    to_pdf()
