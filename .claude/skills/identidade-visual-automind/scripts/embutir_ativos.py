#!/usr/bin/env python3
"""
Gera os blocos base64 da identidade visual AutoMind para HTML autocontido:
@font-face de Hando / Red Hat Display e <img> data-URI do logotipo.

Uso na linha de comando (imprime no stdout, ou grava com --out):
    python embutir_ativos.py fontes                       # Hando 700/500 + Red Hat Display 400/500/700
    python embutir_ativos.py fontes --pesos hando:700,800 rhd:400,700
    python embutir_ativos.py logo                         # cabeçalho: Positivo Preenchido Gradiente Sem Tagline
    python embutir_ativos.py logo --versao capa           # Positivo ... Com Tagline
    python embutir_ativos.py logo --versao simbolo        # Símbolo Preenchido Gradiente (favicon/ícone)
    python embutir_ativos.py logo --produto autoload      # SVG inline da sub-marca (positivo)
    python embutir_ativos.py tudo --out ativos.html       # fontes + logo em um arquivo

Uso como módulo em geradores (`*/Py/_gerar_*.py`):
    import sys; sys.path.insert(0, "<raiz>/.claude/skills/identidade-visual-automind/scripts")
    from embutir_ativos import font_face_css, logo_img, logo_data_uri
    html = f"<style>{font_face_css()}{tokens}</style>... {logo_img(alt='AutoMind')} ..."
"""
from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[4]  # .../scripts -> skill -> skills -> .claude -> repo
ID_VISUAL = RAIZ / "Id_visual"
FONTES = ID_VISUAL / "Fontes"
MARCA_PNG = ID_VISUAL / "_Marca" / "RGB" / "PNG"

# Pesos oficiais para HTML (ver references/ativos.md)
PESOS_PADRAO = {"hando": [700, 500], "rhd": [400, 500, 700]}

HANDO = {
    100: "Hando-HairLine.otf", 200: "Hando-ExtraLight.otf", 300: "Hando-Light.otf",
    400: "Hando-Regular.otf", 500: "Hando-Medium.otf", 600: "Hando-SemiBold.otf",
    700: "Hando-Bold.otf", 800: "Hando-ExtraBold.otf", 900: "Hando-Black.otf",
}
RHD = {
    300: "RedHatDisplay-Light.ttf", 400: "RedHatDisplay-Regular.ttf", 500: "RedHatDisplay-Medium.ttf",
    600: "RedHatDisplay-SemiBold.ttf", 700: "RedHatDisplay-Bold.ttf", 800: "RedHatDisplay-ExtraBold.ttf",
    900: "RedHatDisplay-Black.ttf",
}
RHD_ITALICO = {400: "RedHatDisplay-Italic.ttf", 500: "RedHatDisplay-MediumItalic.ttf", 700: "RedHatDisplay-BoldItalic.ttf"}

LOGOS = {
    "cabecalho": MARCA_PNG / "Horizontal - Positivo - Símbolo Preenchido Gradiente - Sem Tagline.png",
    "capa": MARCA_PNG / "Horizontal - Positivo - Símbolo Preenchido Gradiente - Com Tagline.png",
    "vazado": MARCA_PNG / "Horizontal - Positivo - Símbolo Vazado Gradiente - Sem Tagline.png",
    "negativo": MARCA_PNG / "Horizontal - Negativo - Símbolo Preenchido Gradiente - Sem Tagline.png",
    "negativo-capa": MARCA_PNG / "Horizontal - Negativo - Símbolo Preenchido Gradiente - Com Tagline.png",
    "simbolo": MARCA_PNG / "Símbolo Preenchido Gradiente.png",
    "simbolo-vazado": MARCA_PNG / "Símbolo Vazado Gradiente.png",
    "login": MARCA_PNG / "Login-250-138.png",
}
SUBMARCAS = {
    "autoload": ID_VISUAL / "Marca AutoLoad",
    "automed": ID_VISUAL / "Marca AutoMed",
}


def _b64(caminho: Path) -> str:
    if not caminho.exists():
        sys.exit(f"Ativo não encontrado: {caminho}")
    return base64.b64encode(caminho.read_bytes()).decode("ascii")


def font_face_css(pesos: dict[str, list[int]] | None = None, italico_rhd: list[int] | None = None) -> str:
    """Retorna as regras @font-face em base64. `pesos` = {"hando":[700,500], "rhd":[400,500,700]}."""
    pesos = pesos or PESOS_PADRAO
    regras = []
    for w in pesos.get("hando", []):
        regras.append(
            f'@font-face{{font-family:"Hando";font-weight:{w};font-style:normal;font-display:swap;'
            f'src:url(data:font/otf;base64,{_b64(FONTES / "Hando" / HANDO[w])}) format("opentype");}}'
        )
    for w in pesos.get("rhd", []):
        regras.append(
            f'@font-face{{font-family:"Red Hat Display";font-weight:{w};font-style:normal;font-display:swap;'
            f'src:url(data:font/ttf;base64,{_b64(FONTES / "Red Hat Display" / RHD[w])}) format("truetype");}}'
        )
    for w in italico_rhd or []:
        regras.append(
            f'@font-face{{font-family:"Red Hat Display";font-weight:{w};font-style:italic;font-display:swap;'
            f'src:url(data:font/ttf;base64,{_b64(FONTES / "Red Hat Display" / RHD_ITALICO[w])}) format("truetype");}}'
        )
    return "\n".join(regras) + "\n"


def logo_data_uri(versao: str = "cabecalho") -> str:
    """data:image/png;base64,... do logotipo AutoMind escolhido (chaves em LOGOS)."""
    return "data:image/png;base64," + _b64(LOGOS[versao])


def logo_img(versao: str = "cabecalho", alt: str = "AutoMind", classe: str = "logo", altura_px: int | None = 30) -> str:
    """Tag <img> pronta para o cabeçalho de marca."""
    estilo = f' style="height:{altura_px}px;width:auto"' if altura_px else ""
    return f'<img class="{classe}" src="{logo_data_uri(versao)}" alt="{alt}"{estilo}>'


def favicon_link() -> str:
    """<link rel=icon> com o símbolo em gradiente."""
    return f'<link rel="icon" type="image/png" href="{logo_data_uri("simbolo")}">'


def submarca_svg(produto: str, negativo: bool = False, altura_px: int | None = 36, classe: str = "logo") -> str:
    """SVG inline da sub-marca (AutoLoad/AutoMed), positivo (preto) ou negativo (branco)."""
    pasta = SUBMARCAS[produto.lower()]
    svg = (pasta / ("Versão Negativo.svg" if negativo else "Versão Positivo.svg")).read_text(encoding="utf-8")
    svg = svg.split("?>", 1)[-1].strip()  # remove a declaração XML
    svg = svg.replace("cls-1", f"am-{produto.lower()}-1").replace('id="Layer_1" data-name="Layer 1" ', "")  # evita colisão de classe/id
    estilo = f' style="height:{altura_px}px;width:auto;display:block"' if altura_px else ""
    return svg.replace("<svg ", f'<svg class="{classe}" role="img" aria-label="{produto}"{estilo} ', 1)


def _parse_pesos(itens: list[str] | None) -> dict[str, list[int]]:
    if not itens:
        return PESOS_PADRAO
    out: dict[str, list[int]] = {}
    for item in itens:
        fam, ws = item.split(":")
        out[fam] = [int(w) for w in ws.split(",")]
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("o_que", choices=["fontes", "logo", "favicon", "tudo"])
    ap.add_argument("--pesos", nargs="*", help="ex.: hando:700,500 rhd:400,500,700")
    ap.add_argument("--italico", help="pesos itálicos da Red Hat Display, ex.: 400,700")
    ap.add_argument("--versao", default="cabecalho", choices=sorted(LOGOS))
    ap.add_argument("--produto", choices=sorted(SUBMARCAS), help="SVG inline da sub-marca em vez do logo AutoMind")
    ap.add_argument("--negativo", action="store_true", help="sub-marca em branco (fundo escuro)")
    ap.add_argument("--altura", type=int, default=30)
    ap.add_argument("--out", type=Path)
    a = ap.parse_args()

    partes = []
    if a.o_que in ("fontes", "tudo"):
        italico = [int(w) for w in a.italico.split(",")] if a.italico else None
        partes.append(font_face_css(_parse_pesos(a.pesos), italico))
    if a.o_que in ("logo", "tudo"):
        if a.produto:
            partes.append(submarca_svg(a.produto, a.negativo, a.altura))
        else:
            partes.append(logo_img(a.versao, altura_px=a.altura))
    if a.o_que == "favicon":
        partes.append(favicon_link())

    saida = "\n".join(partes)
    if a.out:
        a.out.write_text(saida, encoding="utf-8")
        print(f"Gravado {a.out} ({len(saida) // 1024} KB)")
    else:
        sys.stdout.write(saida)


if __name__ == "__main__":
    main()
