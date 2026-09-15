# -*- coding: utf-8 -*-
"""Regenera o HTML do Detalhamento das Ondas (0..N) a partir do .md canônico,
reaproveitando EXATAMENTE o <style> + hero do HTML anterior (fidelidade visual).

Uso:
    python _gerar_detalhamento_html.py \
        --md  ../Md/Detalhamento_Ondas0-4_Cronograma_Observabilidade_AutoChecker_2026-06-17.md \
        --tpl ../Html/Detalhamento_Ondas0-3_Cronograma_Observabilidade_AutoChecker_2026-06-15.html \
        --out ../Html/Detalhamento_Ondas0-4_Cronograma_Observabilidade_AutoChecker_2026-06-17.html \
        --titulo "Detalhamento das Ondas 0–4 — AutoChecker" --data 2026-06-17

O template fornece tudo antes de `<div class="wrap">` (head/CSS/hero) e o
fechamento. O corpo vem do markdown renderizado. Blockquotes iniciados por
emoji viram callouts coloridos (⚠️=warn, ❌=bad, ✅=ok, ℹ️=info), igual ao HTML antigo.

Dependência: markdown (pip install markdown).
"""
from __future__ import annotations
import argparse
import re
from pathlib import Path
import markdown as md_lib

WRAP_OPEN = '<div class="wrap">'

# primeiro caractere "visível" do blockquote -> classe de callout
EMOJI_CLASS = [
    (("⚠",), "warn"),                      # ⚠️
    (("❌", "⛔", "\U0001f534"), "bad"),  # ❌ ⛔ \U0001f534
    (("✅", "\U0001f7e2"), "ok"),            # ✅ \U0001f7e2
    (("ℹ", "\U0001f4a1", "\U0001f4cc", "\U0001f535"), "info"),  # ℹ️ \U0001f4a1 \U0001f4cc \U0001f535
]


def classify_blockquotes(html: str) -> str:
    """Adiciona class= aos <blockquote> conforme o emoji-líder do conteúdo."""
    def repl(m: re.Match) -> str:
        inner = m.group(1)
        # primeiro caractere não-espaço do texto interno
        txt = re.sub(r"<[^>]+>", "", inner).lstrip()
        for prefixes, cls in EMOJI_CLASS:
            if txt.startswith(prefixes):
                return f'<blockquote class="{cls}">{inner}</blockquote>'
        return m.group(0)

    return re.sub(r"<blockquote>(.*?)</blockquote>", repl, html, flags=re.DOTALL)


def build(md_path: Path, tpl_path: Path, out_path: Path, titulo: str, data: str) -> None:
    tpl = tpl_path.read_text(encoding="utf-8")
    i = tpl.find(WRAP_OPEN)
    if i == -1:
        raise SystemExit(f"Template sem '{WRAP_OPEN}': {tpl_path}")
    prefix = tpl[:i]  # <head>+<style>+<header class=hero>

    # Atualiza textos do hero/título (substituições diretas e seguras)
    prefix = prefix.replace("Detalhamento das Ondas 0–3 — AutoChecker", titulo)
    prefix = re.sub(r"atualizado \d{4}-\d{2}-\d{2}", f"atualizado {data}", prefix)
    prefix = re.sub(r"Item 6 reavaliado \d{4}-\d{2}-\d{2}",
                    f"Ondas 0–3 em 2026-06-12 · Onda 4 ao vivo em {data}", prefix)

    body_md = md_path.read_text(encoding="utf-8")
    body_html = md_lib.markdown(
        body_md,
        extensions=["tables", "fenced_code", "sane_lists", "toc", "attr_list"],
        output_format="html5",
    )
    body_html = classify_blockquotes(body_html)

    footer = ('<footer class="rodape">Fonte: codigo real + documentacao + Sentry ao vivo '
              f'(automind-qd) · Ondas 0–3 (12/06) + Onda 4 ao vivo ({data}) · '
              'Eduardo / Observabilidade · Automind</footer>')

    out = f"{prefix}{WRAP_OPEN}{body_html}\n{footer}</div></body></html>"
    out_path.write_text(out, encoding="utf-8")
    print(f"OK -> {out_path}  ({len(out):,} bytes, {body_html.count('<blockquote')} blockquotes)")


def main() -> None:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser()
    ap.add_argument("--md", required=True)
    ap.add_argument("--tpl", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--titulo", default="Detalhamento das Ondas 0–4 — AutoChecker")
    ap.add_argument("--data", default="2026-06-17")
    a = ap.parse_args()
    build((here / a.md).resolve(), (here / a.tpl).resolve(),
          (here / a.out).resolve(), a.titulo, a.data)


if __name__ == "__main__":
    main()
