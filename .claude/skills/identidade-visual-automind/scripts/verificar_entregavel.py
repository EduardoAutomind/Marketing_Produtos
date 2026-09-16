#!/usr/bin/env python3
"""
Verifica um entregável HTML da AutoMind contra as regras da identidade visual.

    python verificar_entregavel.py <arquivo.html> [outro.html ...] [--estrito]

Saída: lista de ERROS (violam regra do briefing) e AVISOS (merecem olhar), com código de saída 1
quando há erro (ou, com --estrito, quando há aviso). Regras verificadas:

  E1  falta `color-scheme: light` no CSS
  E2  usa `@media (prefers-color-scheme)` (tema automático) — proibido
  A7  tem `[data-theme="dark"]`: alternância MANUAL é aceita se o padrão continua claro
      (`color-scheme:light` no :root, sem prefers-color-scheme, escolha só via localStorage)
  E3  roxo #44055A / navy #03045E como `color` de título (h1–h6) ou como `background` de bloco
  E4  série/acento em azul (hex com dominância azul fora da paleta) em fill/stroke/background
  E5  dependência externa (link/script/img/url() com http(s)://) — o arquivo deve ser autocontido
  E6  fonte de título não é Hando (ou substituta Manrope) / corpo não é Red Hat Display
  E7  Google Fonts / fontes serifadas ou decorativas declaradas
  A1  hex fora da paleta oficial + apoio + status (lista com contagem)
  E8  fundo do body é escuro (resolve var(--x) do CSS)
  A2  fundo do body não é branco/gelo
  A3  faixa escura: #100F0F (ou preto) usado como background de header/faixa
  A4  tagline grafada sem o ponto mediano (`Simple - Smart - Reliable`, `Simple, Smart, Reliable`…)
  A5  arquivo não referencia logo em base64 (pode estar sem logotipo)
  A6  texto rosa #FA094E em regra sem tamanho grande (usar #C9073F em texto pequeno)
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

PALETA_OFICIAL = {"FA094E", "940755", "44055A", "03045E", "100F0F", "F3F3F0", "FFFFFF"}
PALETA_APOIO = {
    "FFEEF3", "FFF3F7", "F9C6D6", "C9073F", "3F3F45", "6B6B70", "8A8A8F", "E5E5E3", "EFEDEE", "ECEAEB", "D3D0D2",
    "545353", "6F6F6E", "E3E3E1", "D3D3D0", "FBFBFA", "EAEAE8", "8A0C30", "FFF0F4", "FEBFD1",  # neutros e erro derivados da paleta (LP Expopostos)
    # modo noturno (opt-in): gelo diluído no preto, rosa clareado, rampa/status para fundo escuro
    "181717", "242323", "1C1B1B", "2F2E2E", "434242", "BDBDBB", "9C9C9A", "C9C9C6", "232222", "3A3939",
    "FF3D72", "2A1218", "5C1A31", "FF6B8F", "4A1A2A", "7A1F3F", "B31A4F", "3DC28B", "10271D", "E8A93A", "2A2010", "FF5C7A", "2E1218",
    "FBD9E3", "F4A0BB", "EC5C88", "C8104A",  # rampa rosa
    "CF1A66", "6F1170", "231A66",  # ondas de cronograma
    "0F8A5F", "E8F3EE", "A86300", "FBF1DC", "C31035", "FDE8EC",  # status
    "000000",  # preto puro em SVG/print é tolerado
}
PALETA = PALETA_OFICIAL | PALETA_APOIO
# tolerados por serem neutros (cinzas) — a verificação de cinza é por heurística, não por lista
FONTES_TITULO = ("hando", "manrope")
FONTES_SERIFA = ("georgia", "times", "garamond", "serif", "playfair", "merriweather", "lora", "comic", "papyrus", "brush", "pacifico", "lobster")

HEX_RE = re.compile(r"#([0-9a-fA-F]{6})\b")


def _norm(h: str) -> str:
    return h.upper()


def _e_cinza(h: str) -> bool:
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    return max(r, g, b) - min(r, g, b) <= 14


def _lum(h: str) -> float:
    """Luminância relativa (0–1) de um hex de 6 dígitos."""
    def canal(c: int) -> float:
        c /= 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return 0.2126 * canal(r) + 0.7152 * canal(g) + 0.0722 * canal(b)


def _e_azul(h: str) -> bool:
    r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    # azul dominante e saturado: exclui navy oficial (#03045E) que está na paleta
    return b > r + 40 and b > g + 20 and not _e_cinza(h)


def _sem_base64(texto: str) -> str:
    return re.sub(r"base64,[A-Za-z0-9+/=]{100,}", "base64,<...>", texto)


def verificar(caminho: Path) -> tuple[list[str], list[str]]:
    erros: list[str] = []
    avisos: list[str] = []
    bruto = caminho.read_text(encoding="utf-8", errors="replace")
    html = _sem_base64(bruto)
    css = " ".join(re.findall(r"<style[^>]*>(.*?)</style>", html, flags=re.S | re.I))
    css += " " + " ".join(re.findall(r'style="([^"]*)"', html))
    css = re.sub(r"/\*.*?\*/", " ", css, flags=re.S)  # comentários não contam
    css_min = re.sub(r"\s+", "", css).lower()
    # CSS "claro": sem os blocos do tema escuro manual e do @media print (para resolver variáveis do padrão)
    css_claro = re.sub(r':root\[data-theme="dark"\][^{]*\{[^}]*\}', " ", css)
    css_claro = re.sub(r"@media\s*print\s*\{.*?\}\s*\}", " ", css_claro, flags=re.S)

    # E1 / E2 — tema claro fixo
    if "color-scheme:light" not in css_min:
        erros.append("E1 falta `color-scheme: light` no :root (tema claro fixo)")
    if "@media(prefers-color-scheme" in css_min or re.search(r"matchMedia\([^)]*prefers-color-scheme", html):
        erros.append("E2 tema automático via `prefers-color-scheme` — proibido, o arquivo deve abrir sempre branco")
    if "[data-theme" in css_min:
        if "color-scheme:light" in re.sub(r"\s+", "", css_claro).lower() and "localstorage" in html.lower():
            avisos.append("A7 alternância manual de tema detectada — ok se o padrão é claro e a escolha vem só de localStorage (confira o modo noturno no briefing: fundo #100F0F, logo Negativo, rosa chapado como acento)")
        else:
            erros.append("E2 `[data-theme]` sem padrão claro garantido (`color-scheme:light` no :root) ou sem persistência manual — alternância só é aceita como opt-in")

    # E3 — roxo/navy em título ou fundo
    for m in re.finditer(r"(h[1-6][^{]*)\{([^}]*)\}", css, flags=re.I):
        corpo = re.sub(r"\s+", "", m.group(2)).lower()
        if re.search(r"(^|;)color:#(44055a|03045e)", corpo):
            erros.append(f"E3 título em roxo/navy: `{m.group(1).strip()}` — títulos são preto #100F0F")
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        corpo = re.sub(r"\s+", "", m.group(2)).lower()
        if re.search(r"background(-color)?:#(44055a|03045e)(;|$)", corpo):
            erros.append(f"E3 fundo sólido roxo/navy em `{m.group(1).strip()[:60]}`")

    # E4 — azul como série/acento
    azuis: dict[str, int] = {}
    for m in re.finditer(r"(fill|stroke|background(?:-color)?|color)\s*:\s*#([0-9a-fA-F]{6})", html):
        h = _norm(m.group(2))
        if h not in PALETA and _e_azul(h):
            azuis[h] = azuis.get(h, 0) + 1
    for m in re.finditer(r'(fill|stroke)="#([0-9a-fA-F]{6})"', html):
        h = _norm(m.group(2))
        if h not in PALETA and _e_azul(h):
            azuis[h] = azuis.get(h, 0) + 1
    if azuis:
        erros.append("E4 azul usado como cor de série/fundo/texto (fora da paleta): " + ", ".join(f"#{h}×{n}" for h, n in sorted(azuis.items())))

    # E5 — dependências externas
    externos = re.findall(r'(?:<link[^>]+href|<script[^>]+src|<img[^>]+src|url\()\s*=?\s*["\']?(https?://[^"\')\s>]+)', html, flags=re.I)
    if externos:
        erros.append("E5 dependência externa (arquivo deve ser autocontido): " + ", ".join(sorted(set(externos))[:5]))

    # E6 / E7 — fontes
    familias = [f.lower() for f in re.findall(r"font-family\s*:\s*([^;}]+)", css)]
    familias_txt = " ".join(familias)
    tem_hando = any(f in familias_txt for f in FONTES_TITULO)
    tem_rhd = "red hat display" in familias_txt
    if not tem_hando:
        erros.append("E6 nenhuma regra usa Hando (ou Manrope) — títulos devem ser Hando")
    if not tem_rhd:
        erros.append("E6 nenhuma regra usa Red Hat Display — corpo deve ser Red Hat Display")
    if "fonts.googleapis.com" in html or "fonts.gstatic.com" in html:
        erros.append("E7 Google Fonts linkado — embutir as fontes em base64")
    serifas = sorted({s for s in FONTES_SERIFA if s in familias_txt and s != "serif"})
    if serifas or re.search(r"font-family[^;]*[,\s]serif\b(?!.*sans)", css, flags=re.I):
        erros.append("E7 fonte serifada/decorativa declarada: " + ", ".join(serifas or ["serif"]))
    if tem_hando and "@font-face" not in css_min:
        avisos.append("A5 Hando/Red Hat Display sem @font-face — o arquivo depende das fontes instaladas na máquina")

    # A1 — hex fora da paleta
    fora: dict[str, int] = {}
    for m in HEX_RE.finditer(css):
        h = _norm(m.group(1))
        if h not in PALETA and not _e_cinza(h):
            fora[h] = fora.get(h, 0) + 1
    if fora:
        avisos.append("A1 hex fora da paleta (confira se é intencional): " + ", ".join(f"#{h}×{n}" for h, n in sorted(fora.items(), key=lambda x: -x[1])[:12]))

    # E8 / A2 — fundo do body (resolve var(--x) declarada no CSS, um nível)
    variaveis = dict(re.findall(r"(--[a-z0-9-]+)\s*:\s*([^;}]+)", css_claro, flags=re.I))
    for _ in range(3):  # resolve var(--x) que aponta para outra variável
        variaveis = {k: (variaveis.get(v.strip()[4:-1], v) if v.strip().startswith("var(") else v) for k, v in variaveis.items()}
    m = re.search(r"(?:^|[}\s])body\s*\{([^}]*)\}", css)
    if m:
        corpo = re.sub(r"\s+", "", m.group(1)).lower()
        bg = re.search(r"background(?:-color)?:(#[0-9a-f]{3,6}\b|var\(--[a-z0-9-]+\)|white)", corpo)
        if bg:
            v = bg.group(1)
            if v.startswith("var("):
                v = variaveis.get(v[4:-1], v).strip().lower()
            if v in ("white", "#fff"):
                v = "#ffffff"
            hexv = _norm(v[1:]) if re.fullmatch(r"#[0-9a-f]{6}", v) else None
            if hexv and _lum(hexv) < 0.5:
                erros.append(f"E8 body com fundo escuro {v} — entregáveis abrem brancos (#FFFFFF)")
            elif hexv and hexv not in {"FFFFFF", "F3F3F0"}:
                avisos.append(f"A2 body com fundo {v} — esperado #FFFFFF ou #F3F3F0")
            elif not hexv:
                avisos.append(f"A2 body com fundo `{bg.group(1)}` que não consegui resolver — confira se é branco")
        else:
            avisos.append("A2 body sem `background` explícito — declare #FFFFFF")
    else:
        avisos.append("A2 não encontrei regra `body{}` — declare fundo branco e cor de texto")

    # A3 — faixa escura
    for m in re.finditer(r"([^{}]*(?:header|brandhead|hero|topbar|banner|capa|cover)[^{}]*)\{([^}]*)\}", css, flags=re.I):
        corpo = re.sub(r"\s+", "", m.group(2)).lower()
        if re.search(r"background(-color)?:(#100f0f|#000000|#000\b|#1[0-9a-f]{5}|black)", corpo):
            avisos.append(f"A3 faixa escura em `{m.group(1).strip()[:50]}` — cabeçalhos são brancos com régua em gradiente")

    # A4 — tagline
    if re.search(r"Simple\s*[-–,|/•]\s*Smart\s*[-–,|/•]\s*Reliable", html) and "Simple · Smart · Reliable" not in html:
        avisos.append("A4 tagline sem ponto mediano — grafar `Simple · Smart · Reliable`")

    # A5 — logo
    if "data:image/png;base64" not in bruto and "data:image/svg" not in bruto and "<svg" not in html:
        avisos.append("A5 nenhum logotipo/imagem embutido — o cabeçalho de marca deve trazer o logo AutoMind")

    # A6 — rosa cheio em texto pequeno
    for m in re.finditer(r"([^{}]+)\{([^}]*)\}", css):
        corpo = re.sub(r"\s+", "", m.group(2)).lower()
        if re.search(r"(^|;)color:#fa094e", corpo):
            fs = re.search(r"font-size:(\d+(?:\.\d+)?)(px|rem|em)", corpo)
            grande = fs and ((fs.group(2) == "px" and float(fs.group(1)) >= 18) or (fs.group(2) != "px" and float(fs.group(1)) >= 1.15))
            if not grande:
                avisos.append(f"A6 `{m.group(1).strip()[:50]}` usa #FA094E como cor de texto sem tamanho grande — usar #C9073F em texto pequeno")

    return erros, avisos


def main() -> int:
    # console do Windows pode estar em cp1252; força UTF-8 para os símbolos de status
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+", type=Path)
    ap.add_argument("--estrito", action="store_true", help="avisos também falham")
    a = ap.parse_args()

    falhou = False
    for arq in a.arquivos:
        if not arq.exists():
            print(f"✗ {arq}: não encontrado")
            falhou = True
            continue
        erros, avisos = verificar(arq)
        status = "✓" if not erros and not (a.estrito and avisos) else "✗"
        print(f"{status} {arq}  —  {len(erros)} erro(s), {len(avisos)} aviso(s)")
        for e in erros:
            print(f"   ERRO  {e}")
        for w in avisos:
            print(f"   aviso {w}")
        if erros or (a.estrito and avisos):
            falhou = True
    return 1 if falhou else 0


if __name__ == "__main__":
    sys.exit(main())
