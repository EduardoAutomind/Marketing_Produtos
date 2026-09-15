# -*- coding: utf-8 -*-
"""Regenera o HTML e o PDF do Roadmap de Observabilidade do AutoChecker
a partir do Roadmap_Observabilidade_AutoChecker.md (modelo de cards .etapa,
faixas de onda, hero e callouts) e imprime via Edge/Chrome headless --print-to-pdf.
Dependências: markdown (stdlib + markdown)."""
from __future__ import annotations
import re, subprocess, sys
from pathlib import Path
from urllib.parse import urljoin
from urllib.request import pathname2url
import markdown as md_lib

ROOT = Path(__file__).resolve().parent
MD   = ROOT / "Roadmap_Observabilidade_AutoChecker.md"
HTML = ROOT / "Roadmap_Observabilidade_AutoChecker.html"
PDF  = ROOT / "Roadmap_Observabilidade_AutoChecker.pdf"

BROWSERS = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
]

CSS = r"""
  :root{
    --bg:#f7f8fa; --ink:#1c2330; --muted:#5b6678; --line:#e3e7ee;
    --card:#ffffff; --accent:#2b5cff; --accent-soft:#eef2ff;
    --gate:#b4232a; --gate-soft:#fff1f1; --gate-line:#f2c4c4;
    --ok:#1a7f4b; --ok-soft:#e7f6ee; --warn:#9a6700; --warn-soft:#fff7e0;
    --new:#5a2a8c; --new-soft:#f3ebfb; --bad:#b4232a;
    --pend:#8a5a00; --pend-soft:#fff4d6; --pend-line:#e9cf8a;
    --w0:#b4232a; --w1:#1e6fb8; --w2:#0f8a7e; --w3:#c06700; --w4:#6a4bbf; --w5:#1a7f4b; --w6:#39506b;
  }
  *{box-sizing:border-box}
  html{scroll-behavior:smooth}
  body{margin:0;background:var(--bg);color:var(--ink);
    font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
  .wrap{max-width:1080px;margin:0 auto;padding:32px 24px 80px;}
  header.hero{background:linear-gradient(135deg,#1c2330,#2b3a55);color:#fff;border-radius:16px;
    padding:34px 36px;margin-bottom:28px;box-shadow:0 6px 24px rgba(28,35,48,.18);}
  header.hero h1{margin:0 0 6px;font-size:27px;letter-spacing:-.3px}
  header.hero p{margin:4px 0;color:#c8d2e6;font-size:14px}
  header.hero .meta{margin-top:14px;display:flex;flex-wrap:wrap;gap:8px}
  header.hero .pill{background:rgba(255,255,255,.12);border:1px solid rgba(255,255,255,.22);
    border-radius:999px;padding:4px 12px;font-size:12.5px}
  h2{font-size:21px;margin:38px 0 14px;padding-bottom:8px;border-bottom:2px solid var(--line)}
  h3{font-size:17px;margin:26px 0 8px}
  a{color:var(--accent);text-decoration:none}
  a:hover{text-decoration:underline}
  code{background:#eef1f6;border:1px solid #e0e5ee;border-radius:5px;padding:1px 5px;
    font:13px/1.4 "SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace;color:#34405a}
  .lead{font-size:15.5px;color:var(--muted);max-width:78ch}

  /* callouts (blockquotes do markdown viram callouts) */
  blockquote{border-radius:12px;padding:14px 18px;margin:16px 0;border:1px solid #d3deff;
    background:var(--accent-soft);color:#33405a}
  blockquote p{margin:5px 0}
  blockquote.gate{background:var(--gate-soft);border-color:var(--gate-line)}
  blockquote.gate strong{color:var(--gate)}
  blockquote.pend{background:var(--pend-soft);border-color:var(--pend-line);color:#6b5012}

  /* tables */
  table{border-collapse:collapse;width:100%;margin:14px 0;font-size:13px;background:var(--card);
    border:1px solid var(--line);border-radius:10px;overflow:hidden}
  th,td{padding:8px 10px;text-align:left;border-bottom:1px solid var(--line);vertical-align:top}
  th{background:#f0f3f8;font-weight:700;font-size:12.5px;color:#33405a}
  tr:last-child td{border-bottom:0}

  /* wave header band */
  .wave{border-radius:14px;padding:18px 22px;margin:34px 0 6px;color:#fff}
  .wave h2{color:#fff;border:0;margin:0;font-size:20px}
  .wave p{margin:6px 0 0;color:rgba(255,255,255,.92);font-size:13.5px}
  .wave .tag{display:inline-block;background:rgba(255,255,255,.18);border-radius:999px;
    padding:2px 11px;font-size:12px;margin-bottom:8px}
  .w-0{background:linear-gradient(135deg,#8e1a20,#b4232a)}
  .w-1{background:linear-gradient(135deg,#155a96,#1e6fb8)}
  .w-2{background:linear-gradient(135deg,#0b6b62,#0f8a7e)}
  .w-3{background:linear-gradient(135deg,#9a5200,#c06700)}
  .w-4{background:linear-gradient(135deg,#523a96,#6a4bbf)}
  .w-5{background:linear-gradient(135deg,#13633a,#1a7f4b)}
  .w-6{background:linear-gradient(135deg,#2b3d52,#39506b)}

  /* etapa card */
  .etapa{background:var(--card);border:1px solid var(--line);border-left:5px solid var(--accent);
    border-radius:12px;padding:18px 22px;margin:16px 0;box-shadow:0 1px 3px rgba(28,35,48,.05)}
  .etapa.w0{border-left-color:var(--w0)}.etapa.w1{border-left-color:var(--w1)}
  .etapa.w2{border-left-color:var(--w2)}.etapa.w3{border-left-color:var(--w3)}
  .etapa.w4{border-left-color:var(--w4)}.etapa.w5{border-left-color:var(--w5)}
  .etapa.w6{border-left-color:var(--w6)}
  .etapa .eh{display:flex;align-items:baseline;gap:10px;flex-wrap:wrap;margin-bottom:4px}
  .etapa .num{font-size:13px;font-weight:800;color:#fff;background:var(--accent);
    border-radius:8px;padding:3px 9px;min-width:30px;text-align:center}
  .etapa.w0 .num{background:var(--w0)}.etapa.w1 .num{background:var(--w1)}
  .etapa.w2 .num{background:var(--w2)}.etapa.w3 .num{background:var(--w3)}
  .etapa.w4 .num{background:var(--w4)}.etapa.w5 .num{background:var(--w5)}
  .etapa.w6 .num{background:var(--w6)}
  .etapa h3{margin:0;font-size:16.5px;flex:1 1 60%}
  .badges{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 12px}
  .b{font-size:11.5px;border-radius:999px;padding:2px 9px;border:1px solid var(--line);background:#f3f5f9;color:#46526b}
  .b.layer{background:#eef2ff;border-color:#d3deff;color:#2b3a7a}
  .b.esf{background:#f0f3f8}
  .b.ok{background:var(--ok-soft);border-color:#bfe6cf;color:var(--ok)}
  .b.warn{background:var(--warn-soft);border-color:#ecd9a3;color:var(--warn)}
  .b.bad{background:var(--gate-soft);border-color:var(--gate-line);color:var(--bad)}
  .b.new{background:var(--new-soft);border-color:#dcc6f0;color:var(--new)}
  .field{margin:9px 0}
  .field .lbl{font-weight:700;font-size:12.5px;text-transform:uppercase;letter-spacing:.4px;color:var(--muted);display:block;margin-bottom:1px}
  .field p{margin:3px 0}
  .field ol,.field ul{margin:4px 0;padding-left:22px}
  .field li{margin:3px 0}
  .src{color:var(--muted);font-size:12px;font-style:italic;margin:8px 0}
  .dep{font-size:13px}
  .done{background:var(--ok-soft);border:1px solid #bfe6cf;border-radius:8px;padding:8px 12px;font-size:13.5px;margin:9px 0}
  .done .lbl{color:var(--ok);font-weight:700;text-transform:uppercase;font-size:12px;letter-spacing:.4px;margin-right:6px}
  .pendln{background:var(--pend-soft);border:1px dashed var(--pend-line);border-radius:8px;padding:8px 12px;font-size:13px;color:#6b5012;margin:9px 0}
  .pendln .lbl{color:var(--pend);font-weight:700;text-transform:uppercase;font-size:12px;letter-spacing:.4px;margin-right:6px}
  section.block{margin:6px 0}
  footer{margin-top:50px;padding-top:18px;border-top:1px solid var(--line);color:var(--muted);font-size:12.5px}
  @page{size:A4;margin:14mm 12mm}
  @media print{
    body{background:#fff}
    .wrap{max-width:none;padding:0}
    header.hero{box-shadow:none;-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .etapa,.wave,blockquote,table,.wave h2,.done,.pendln,.b,.num{-webkit-print-color-adjust:exact;print-color-adjust:exact}
    .etapa{break-inside:avoid;box-shadow:none}
    .wave{break-after:avoid;break-before:auto}
    h2,h3{break-after:avoid}
    table,tr{break-inside:avoid}
    a{color:var(--ink)}
  }
"""

def md(text: str) -> str:
    text = re.sub(r'(?m)^\s*---\s*$', '', text).strip()
    if not text:
        return ""
    return md_lib.markdown(text, extensions=["tables", "fenced_code", "sane_lists"])

def md_inline(text: str) -> str:
    h = md(text).strip()
    m = re.fullmatch(r"<p>(.*)</p>", h, flags=re.S)
    return m.group(1).strip() if m else h

def style_blockquotes(html: str) -> str:
    def repl(m):
        block = m.group(0)
        up = block.upper()
        if "GATE" in up:
            return block.replace("<blockquote>", '<blockquote class="gate">', 1)
        if "PENDENTE" in up or "REVALID" in up:
            return block.replace("<blockquote>", '<blockquote class="pend">', 1)
        return block
    return re.sub(r"<blockquote>.*?</blockquote>", repl, html, flags=re.S)

VERIF = [("✅", "ok"), ("⚠️", "warn"), ("❌", "bad"), ("🆕", "new")]

def etapa_card(title: str, body: str, wave) -> str:
    mnum = re.match(r"Etapa\s+(\d+)\s*[—-]\s*(.*)", title.strip(), flags=re.S)
    num = mnum.group(1) if mnum else "?"
    rest = md_inline(mnum.group(2) if mnum else title)
    wcls = f"w{wave}" if wave is not None else ""

    labels = ["**O problema:**", "**Por que importa:**", "**Como resolver:**",
              "**Depende de:**", "**PRONTO quando:**", "**O que ainda não sei:**"]
    pos = {}
    for lab in labels:
        i = body.find(lab)
        pos[lab] = i
    first = min((i for i in pos.values() if i >= 0), default=len(body))
    meta = body[:first]

    def seg(lab, nexts):
        i = pos.get(lab, -1)
        if i < 0:
            return ""
        start = i + len(lab)
        ends = [pos[n] for n in nexts if pos.get(n, -1) > i]
        end = min(ends) if ends else len(body)
        return body[start:end].strip()

    problema = seg(labels[0], labels[1:])
    importa  = seg(labels[1], labels[2:])
    resolver = seg(labels[2], labels[3:])
    depende  = seg(labels[3], labels[4:])
    pronto   = seg(labels[4], labels[5:])
    naosei   = seg(labels[5], [])

    # extrai a linha de fonte *(...)* de dentro de "Como resolver"
    src = ""
    msrc = re.search(r"\*\((.+?)\)\*", resolver, flags=re.S)
    if msrc:
        src = msrc.group(1).strip()
        resolver = resolver[:msrc.start()].strip()

    # meta -> badges
    def grab(pat):
        m = re.search(pat, meta)
        return m.group(1).strip() if m else ""
    camada = grab(r"\*\*Camada:\*\*\s*(.+?)\s*·")
    esf    = grab(r"\*\*Esforço:\*\*\s*(.+?)\s*·")
    sem    = grab(r"\*\*Semanas?:\*\*\s*(.+?)\s*·")
    verif  = grab(r"\*\*Verificação:\*\*\s*(.+)")
    vcls = "ok"
    for emo, cls in VERIF:
        if emo in verif:
            vcls = cls
            break

    badges = []
    if camada: badges.append(f'<span class="b layer">{md_inline(camada)}</span>')
    if esf:    badges.append(f'<span class="b esf">Esforço {md_inline(esf)}</span>')
    if sem:    badges.append(f'<span class="b">Sem {md_inline(sem)}</span>')
    if verif:  badges.append(f'<span class="b {vcls}">{md_inline(verif)}</span>')

    parts = [f'<div class="etapa {wcls}">']
    parts.append(f'<div class="eh"><span class="num">{num}</span><h3>{rest}</h3></div>')
    parts.append('<div class="badges">' + "".join(badges) + '</div>')
    if problema: parts.append(f'<div class="field"><span class="lbl">O problema</span>{md(problema)}</div>')
    if importa:  parts.append(f'<div class="field"><span class="lbl">Por que importa</span>{md(importa)}</div>')
    if resolver: parts.append(f'<div class="field"><span class="lbl">Como resolver</span>{style_blockquotes(md(resolver))}</div>')
    if src:      parts.append(f'<div class="src">{md_inline(src)}</div>')
    if depende:  parts.append(f'<div class="field dep"><span class="lbl">Depende de</span>{md(depende)}</div>')
    if pronto:   parts.append(f'<div class="done"><span class="lbl">Pronto quando</span>{md_inline(pronto)}</div>')
    if naosei:   parts.append(f'<div class="pendln"><span class="lbl">O que ainda não sei</span>{md_inline(naosei)}</div>')
    parts.append('</div>')
    return "\n".join(parts)

def wave_band(n: int, title: str, body: str) -> str:
    intro = ""
    mq = re.search(r"(?m)^>\s?(.*(?:\n>.*)*)", body)
    if mq:
        intro = md_inline(re.sub(r"(?m)^>\s?", "", mq.group(0)))
    return (f'<div class="wave w-{n}"><span class="tag">Onda {n}</span>'
            f'<h2>{md_inline(title)}</h2>' + (f'<p>{intro}</p>' if intro else '') + '</div>')

def hero(title: str, body: str) -> str:
    body_txt = re.sub(r"(?m)^>\s?", "", body).strip()
    body_txt = re.sub(r"(?m)^\s*---\s*$", "", body_txt).strip()
    paras = [md_inline(p) for p in re.split(r"\n\s*\n", body_txt) if p.strip()]
    pmain = paras[0] if paras else ""
    pmeta = " ".join(paras[1:]) if len(paras) > 1 else ""
    pills = ["Sentry · org automind-qd", "31 etapas · 7 ondas",
             "Onda 0 = GATE", "Verificado no código · 10/06/2026"]
    pill_html = "".join(f'<span class="pill">{p}</span>' for p in pills)
    return (f'<header class="hero"><h1>{md_inline(title)}</h1>'
            f'<p>{pmain}</p>' + (f'<p>{pmeta}</p>' if pmeta else '') +
            f'<div class="meta">{pill_html}</div></header>')

def build_html(src_md: str) -> str:
    heads = list(re.finditer(r"(?m)^(#{1,3})\s+(.*)$", src_md))
    chunks = []
    for i, m in enumerate(heads):
        level = len(m.group(1))
        title = m.group(2).strip()
        start = m.end()
        end = heads[i + 1].start() if i + 1 < len(heads) else len(src_md)
        body = src_md[start:end]
        chunks.append((level, title, body))

    out = []
    wave = None
    for level, title, body in chunks:
        t = title.strip()
        if level == 1 and t.lower().startswith("roadmap"):
            out.append(hero(t, body))
        elif level == 1 and t.upper().startswith("ONDA"):
            mw = re.search(r"ONDA\s+(\d)", t.upper())
            wave = int(mw.group(1)) if mw else None
            out.append(wave_band(wave, t, body))
        elif level == 2 and t.startswith("Etapa"):
            out.append(etapa_card(t, body, wave))
        elif level == 1:
            out.append(f'<h2>{md_inline(t)}</h2>' + style_blockquotes(md(body)))
        elif level == 2:
            out.append('<section class="block"><h2>' + md_inline(t) + '</h2>' +
                       style_blockquotes(md(body)) + '</section>')
        else:  # level 3
            out.append('<h3>' + md_inline(t) + '</h3>' + style_blockquotes(md(body)))

    footer = ('<footer>Roadmap gerado em 10/06/2026, verificado <code>arquivo:linha</code> contra o '
              'código real em <code>C:\\Projetos\\automind-obs\\Produtos\\Autochecker\\</code>. '
              'Org Sentry <code>automind-qd</code>. Nenhum item deve ser implementado sem revisão do time de arquitetura.</footer>')

    return ("<!doctype html><html lang=\"pt-BR\"><head><meta charset=\"utf-8\">"
            "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">"
            "<title>Roadmap de Execução — Observabilidade do AutoChecker</title>"
            f"<style>{CSS}</style></head><body><div class=\"wrap\">"
            + "\n".join(out) + footer + "</div></body></html>")

def find_browser() -> str:
    for c in BROWSERS:
        if Path(c).exists():
            return c
    sys.exit("Nenhum navegador (Edge/Chrome) encontrado para gerar o PDF.")

def main() -> None:
    html = build_html(MD.read_text(encoding="utf-8"))
    HTML.write_text(html, encoding="utf-8")
    print(f"HTML: {HTML.name} ({HTML.stat().st_size/1024:.1f} KB)")

    browser = find_browser()
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
    main()
