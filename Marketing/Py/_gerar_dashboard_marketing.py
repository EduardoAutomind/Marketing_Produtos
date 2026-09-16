#!/usr/bin/env python3
"""
Gera o Dashboard de Marketing AutoMind (HTML autocontido) a partir do template
`_dashboard_marketing_src.html`, embutindo fontes (Hando / Red Hat Display) e o
logotipo em base64 via a skill `identidade-visual-automind`.

    python Marketing/Py/_gerar_dashboard_marketing.py            # grava Html/Dashboard_Marketing_AutoMind_<data>.html
    python Marketing/Py/_gerar_dashboard_marketing.py --data 2026-09-16

Placeholders do template: {{FONTES}}, {{LOGO_SRC}}, {{LOGO_NEG_SRC}} (modo noturno), {{FAVICON}}, {{DATA}}.
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]
SKILL = RAIZ / ".claude" / "skills" / "identidade-visual-automind" / "scripts"
sys.path.insert(0, str(SKILL))
from embutir_ativos import favicon_link, font_face_css, logo_data_uri  # noqa: E402

TEMPLATE = AQUI / "_dashboard_marketing_src.html"
SAIDA_DIR = AQUI.parent / "Html"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--data", default=date.today().isoformat(), help="data no nome do arquivo (AAAA-MM-DD)")
    a = ap.parse_args()

    html = TEMPLATE.read_text(encoding="utf-8")
    html = (
        html.replace("{{FONTES}}", font_face_css({"hando": [700, 800], "rhd": [400, 500, 700]}))
        .replace("{{LOGO_SRC}}", logo_data_uri("cabecalho"))
        .replace("{{LOGO_NEG_SRC}}", logo_data_uri("negativo"))
        .replace("{{FAVICON}}", favicon_link())
        .replace("{{DATA}}", a.data)
    )
    saida = SAIDA_DIR / f"Dashboard_Marketing_AutoMind_{a.data}.html"
    saida.write_text(html, encoding="utf-8")
    print(f"Gravado {saida.relative_to(RAIZ)} ({saida.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
