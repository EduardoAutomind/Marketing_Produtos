# -*- coding: utf-8 -*-
"""
Gera as versoes HTML (tema dark-nao-tao-escuro, identidade AutoMind) das duas
saidas sobre o IntegrationLog do AutoChecker, a partir dos .md em ../Md/.
"""
import re
import markdown
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
MD = BASE / "Md"
HTML = BASE / "Html"

CSS = """
  @import url('https://fonts.googleapis.com/css2?family=Red+Hat+Display:ital,wght@0,400;0,500;0,700;0,900;1,400&display=swap');
  :root{
    --am-rosa:#FA094E; --am-magenta:#940755; --am-roxo:#44055A;
    --am-navy:#03045E; --am-preto:#100F0F; --am-offwhite:#F3F3F0;
    --am-gradiente-h:linear-gradient(90deg,#FA094E 0%,#03045E 100%);
    --card:#ffffff; --line:#e4e2dd;
    --ok:#1f8a4c; --warn:#b8860b; --crit:#FA094E;
  }
  *{box-sizing:border-box;}
  html{scroll-behavior:smooth;}
  body{font-family:"Red Hat Display",system-ui,sans-serif;color:var(--am-preto);
    background:var(--am-offwhite); margin:0; line-height:1.6; font-size:16px;}
  .topbar{height:8px; background:var(--am-gradiente-h);}
  header{padding:34px 7vw 22px; border-bottom:1px solid var(--line);}
  .wordmark{font-weight:900; text-transform:uppercase; letter-spacing:.20em;
    color:var(--am-roxo); font-size:15px;}
  .wordmark .dot{color:var(--am-rosa);}
  .tagline{font-size:11px; letter-spacing:.32em; text-transform:uppercase;
    color:var(--am-navy); opacity:.7; margin-top:2px;}
  h1{font-weight:900; color:var(--am-roxo); font-size:30px; line-height:1.2;
    margin:18px 0 6px; letter-spacing:.01em;}
  .sub{color:var(--am-navy); font-size:14px; opacity:.85;}
  .pill{display:inline-block; background:var(--am-roxo); color:#fff; font-size:11px;
    font-weight:700; letter-spacing:.08em; text-transform:uppercase;
    padding:4px 11px; border-radius:999px; margin:8px 6px 0 0;}
  .pill.alt{background:var(--am-rosa);}
  main{padding:14px 7vw 60px; max-width:1080px;}
  h2{font-weight:700; color:var(--am-roxo); font-size:21px; margin:38px 0 10px;
    padding-top:14px; border-top:2px solid var(--am-rosa); display:inline-block;}
  h3{font-weight:700; color:var(--am-navy); font-size:16px; margin:22px 0 6px;}
  p{margin:10px 0;}
  a{color:var(--am-rosa); text-decoration:none;} a:hover{text-decoration:underline;}
  ul,ol{margin:10px 0; padding-left:22px;} li{margin:5px 0;}
  code{font-family:"SFMono-Regular",Consolas,monospace; background:#efeeea;
    padding:1px 6px; border-radius:5px; font-size:.88em; color:var(--am-magenta);}
  pre{background:var(--am-preto); color:#f3f3f0; padding:14px 16px; border-radius:12px;
    overflow:auto; font-size:13px; line-height:1.5;}
  pre code{background:none; color:inherit; padding:0;}
  hr{border:none; border-top:1px solid var(--line); margin:26px 0;}
  blockquote{border-left:4px solid var(--am-rosa); background:#fff; border-radius:0 12px 12px 0;
    padding:8px 18px; margin:14px 0; color:var(--am-navy); font-size:14.5px;}
  table{border-collapse:collapse; width:100%; margin:14px 0; font-size:14px;}
  th,td{text-align:left; padding:9px 12px; border-bottom:1px solid var(--line); vertical-align:top;}
  th{background:#efeeea; color:var(--am-roxo); font-weight:700; font-size:12px;
    text-transform:uppercase; letter-spacing:.05em;}
  tr:last-child td{border-bottom:none;}
  .tldr{background:linear-gradient(0deg,#fff,#fff) padding-box,var(--am-gradiente-h) border-box;
    border:2px solid transparent; border-radius:16px; padding:16px 22px; font-size:16px; margin:18px 0;}
  .flag{font-weight:700; font-size:12px; padding:1px 7px; border-radius:6px; white-space:nowrap;}
  .f-sei{background:#e3f3e9; color:var(--ok);}
  .f-parc{background:#fbf2da; color:var(--warn);}
  .f-nao{background:#fde4ea; color:var(--crit);}
  footer{padding:24px 7vw 50px; color:var(--am-navy); opacity:.7; font-size:12.5px;
    border-top:1px solid var(--line);}
"""

SHELL = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} · AutoMind</title>
<style>{css}</style>
</head>
<body>
<div class="topbar"></div>
<header>
  <div class="wordmark">AUTOMIND<span class="dot">.</span></div>
  <div class="tagline">Simple · Smart · Reliable</div>
  <h1>{h1}</h1>
  <div class="sub">{sub}</div>
  {pills}
</header>
<main>
{body}
</main>
<footer>{footer}</footer>
</body>
</html>
"""


def colorize_flags(html: str) -> str:
    """Pinta as flags Sei/Parcial/Nao e badges de severidade nas celulas/texto."""
    html = re.sub(r"\bParcial\b", '<span class="flag f-parc">Parcial</span>', html)
    html = re.sub(r"\bN[aã]o sei\b", '<span class="flag f-nao">Não sei</span>', html)
    # "Sei" isolado (evita casar dentro de palavras) — so quando seguido de fronteira
    html = re.sub(r"(?<![\w>])Sei(?![\w<])", '<span class="flag f-sei">Sei</span>', html)
    return html


def md_to_html(md_text: str) -> str:
    html = markdown.markdown(
        md_text,
        extensions=["tables", "fenced_code", "sane_lists", "attr_list"],
    )
    return colorize_flags(html)


def strip_front(md_text: str):
    """Remove o bloco de titulo/metadata inicial ja representado no header."""
    return md_text


def build(md_file, title, h1, sub, pills, footer):
    raw = (MD / md_file).read_text(encoding="utf-8")
    # remove a primeira linha "# ..." (vira o h1 do header)
    lines = raw.splitlines()
    if lines and lines[0].startswith("# "):
        lines = lines[1:]
    body_md = "\n".join(lines).lstrip("\n")
    body = md_to_html(body_md)
    out = SHELL.format(
        title=title, css=CSS, h1=h1, sub=sub,
        pills="\n  ".join(f'<span class="pill{c}">{t}</span>' for t, c in pills),
        body=body, footer=footer,
    )
    dest = HTML / (Path(md_file).stem + ".html")
    dest.write_text(out, encoding="utf-8")
    print("ok ->", dest.name, f"({len(out)} bytes)")


build(
    "Mudancas_AutoChecker_Relevantes_Observabilidade_AzureDevOps_2026-06-30.md",
    "Mudanças AutoChecker relevantes p/ Observabilidade",
    "Mudanças no código do AutoChecker<br>relevantes para <span style='color:var(--am-rosa)'>Observabilidade</span>",
    "Azure DevOps · org automindautomacao · janela 08→30/06/2026 · gerado 2026-06-30",
    [("Análise de código", ""), ("Azure DevOps", " alt"), ("IntegrationLog", "")],
    "Análise baseada na leitura direta dos diffs dos PRs 15213/15214 e do modelo/serializer IntegrationLog · AutoMind · Observabilidade AutoMind · 2026-06-30",
)

build(
    "Auditoria_LGPD_IntegrationLog_AutoChecker_2026-06-30.md",
    "Auditoria LGPD — IntegrationLog AutoChecker",
    "Auditoria LGPD — <span style='color:var(--am-rosa)'>IntegrationLog</span><br>do AutoChecker",
    "Lei nº 13.709/2018 · ancorada artigo-a-artigo · gerado 2026-06-30",
    [("Conformidade LGPD", ""), ("Parcial → não-conformidades", " alt"), ("Etapa 7 correlata", "")],
    "Toda afirmação legal ancorada em reference/Lgpd.md (ed. Senado, jun/2024) · flags Sei/Parcial/Não sei sem suposição · AutoMind · 2026-06-30",
)
