# Paleta AutoMind — papel de cada cor e contraste medido

Contraste WCAG calculado sobre branco `#FFFFFF` (entre parênteses: sobre gelo `#F3F3F0`). AA para texto normal exige ≥ 4,5:1; texto grande (≥ 18 px ou 14 px bold) exige ≥ 3:1.

## Oficial (Resumo Identidade Visual AutoMind.png)

| Nome | HEX | RGB | Contraste | Papel no entregável |
|---|---|---|---|---|
| Rosa AutoMind | `#FA094E` | 250, 9, 78 | 4,03 (3,62) | Acento: métrica prioritária, série DT, botão principal, régua. **Texto só ≥ 18 px** |
| Magenta | `#940755` | 148, 7, 85 | 8,68 | Só dentro do gradiente |
| Roxo | `#44055A` | 68, 5, 90 | 14,84 | Só dentro do gradiente. **Não** é cor de título/fundo |
| Navy | `#03045E` | 3, 4, 94 | 17,75 | Só dentro do gradiente. **Não** é cor de título/fundo |
| Preto AutoMind | `#100F0F` | 16, 15, 15 | 19,14 | Texto e títulos. Não usar em faixas grandes de cabeçalho |
| Branco gelo | `#F3F3F0` | 243, 243, 240 | — | Fundo de apoio (pré, áreas secundárias, fundo de reunião) |
| Branco | `#FFFFFF` | 255, 255, 255 | — | Fundo principal de qualquer entregável |

## Apoio (derivados — briefing §3.3 + validação no Dashboard de Marketing 2026-09-16)

| Nome | HEX | Contraste | Uso |
|---|---|---|---|
| Rosa lavado 1 | `#FFEEF3` | — | Fundo de card/bloco em destaque, callout info, chip "prioritário" |
| Rosa lavado 2 | `#FFF3F7` | — | Linha/área em realce leve; topo do gradiente de card prioritário |
| Rosa linha | `#F9C6D6` | — | Borda de card prioritário |
| Rosa texto | `#C9073F` | 5,86 (5,27) | Rosa em texto pequeno, links, foco. Substitui `#FA094E` abaixo de 18 px |
| Cinza-chumbo | `#3F3F45` | 10,46 | Série HT; texto de apoio forte |
| Cinza texto (tinta) | `#545353` | 6,9 | Texto secundário, subtítulos, rodapé · 70% preto no gelo |
| Cinza terciário (tinta fraca) | `#6F6F6E` | 4,5 | Legendas, eixos, rótulos · 58% preto · limite AA |
| Cinza médio (briefing) | `#8A8A8F` | 3,44 | Tolerado só em elementos não textuais. Reprova AA em texto |
| Cinza linha | `#E3E3E1` | — | Borda de cartão · 7% preto (`#E5E5E3` do briefing é equivalente) |
| Cinza linha forte | `#D3D3D0` | — | Borda em hover, controles · 14% preto |
| Papel | `#FBFBFA` | — | Fundo de cartão · 30% gelo sobre branco |
| Cinza fio | `#EAEAE8` | — | Divisores finos, chips neutros · 4% preto |
| Erro (tinta) | `#8A0C30` | 8,7 | Mensagem de erro em texto pequeno · rosa + 48% preto |
| Grade / eixo | `#ECEAEB` / `#D3D0D2` | — | Gráficos SVG |

> O briefing lista `#8A8A8F` como "texto secundário". Medido, ele dá 3,4:1 sobre branco e reprova AA em corpo de texto. Os neutros adotados são os da LP Expopostos 2026: o próprio preto `#100F0F` diluído no gelo `#F3F3F0`, na proporção anotada — nenhum cinza inventado. Mesmo raciocínio para `#C9073F` (rosa texto) e `#8A0C30` (erro), ausentes do briefing mas necessários para rosa legível em texto pequeno.

## Séries e rampas

| Uso | Cores |
|---|---|
| Duas séries (DT / HT) | `#FA094E` / `#3F3F45` — par validado para daltonismo (ΔE 12,7 protan). **Sem azul** |
| Rampa ordinal (funil, intensidade) | `#FBD9E3 → #F4A0BB → #EC5C88 → #C8104A` |
| Ondas de cronograma (7 tons) | `#FA094E → #CF1A66 → #940755 → #6F1170 → #44055A → #231A66 → #03045E` |
| Terceira série (raro) | `#8A8A8F` (cinza médio). Se precisar de mais que três, repense o gráfico |

## Semântica de status (só em pílulas, badges e callouts pequenos)

| Estado | Texto | Fundo |
|---|---|---|
| ok / concluído | `#0F8A5F` | `#E8F3EE` |
| atenção / em risco | `#A86300` | `#FBF1DC` |
| crítico / erro | `#C31035` | `#FDE8EC` |
| info / neutro | `#C9073F` | `#FFEEF3` (rosa lavado — **não azul**) |

## Gradientes

```css
/* Em HTML: sempre 2 stops. Magenta e roxo são a interpolação, não paradas. */
background: linear-gradient(45deg,  #FA094E 0%, #03045E 100%);  /* botão principal, eyebrow/texto recortado */
background: linear-gradient(90deg,  #FA094E 0%, #03045E 100%);  /* régua fina horizontal */
background: linear-gradient(180deg, #FA094E 0%, #03045E 100%);  /* barra lateral de 4 px */
background: linear-gradient(45deg,  #FA094E 0%, #940755 100%);  /* metade clara: número-herói sobre fundo claro */
```

O gradiente é do símbolo. Em HTML aceita-se como acento: régua ≤ 4 px, barra de 4 px em cartão, botão principal, eyebrow/número-herói com `background-clip:text` e ondas de cronograma. Nunca em fundo inteiro nem texto corrido.

## Constantes para Python (openpyxl / reportlab / geradores)

```python
AM = {
    "rosa": "FA094E", "magenta": "940755", "roxo": "44055A", "navy": "03045E",
    "preto": "100F0F", "gelo": "F3F3F0", "branco": "FFFFFF",
    "rosa_wash1": "FFEEF3", "rosa_wash2": "FFF3F7", "rosa_line": "F9C6D6", "rosa_text": "C9073F",
    "cinza_chumbo": "3F3F45", "cinza_texto": "545353", "cinza_fraco": "6F6F6E",
    "cinza_linha": "E3E3E1", "cinza_linha_forte": "D3D3D0", "papel": "FBFBFA", "cinza_fio": "EAEAE8", "erro_tinta": "8A0C30",
    "dt": "FA094E", "ht": "3F3F45",
    "ok": "0F8A5F", "ok_bg": "E8F3EE", "warn": "A86300", "warn_bg": "FBF1DC",
    "crit": "C31035", "crit_bg": "FDE8EC",
}
ONDAS = ["FA094E", "CF1A66", "940755", "6F1170", "44055A", "231A66", "03045E"]
RAMPA_ROSA = ["FBD9E3", "F4A0BB", "EC5C88", "C8104A"]
# openpyxl: PatternFill("solid", fgColor=AM["rosa_wash1"]); Font(color=AM["preto"], name="Red Hat Display")
```

Fills herdados dos cronogramas `.xlsx` (esforço P/M/G = `DBEAFE`/`FEF9C3`/`FED7AA`, capa navy): exceção documentada, mantida só nesses três arquivos por consistência entre produtos.

## Exemplos de uso correto

- Card prioritário: borda `#F9C6D6`, fundo `#FFF3F7 → #FFFFFF`, rótulo "PRIORITÁRIA" em `#C9073F` sobre `#FFEEF3`, número em Hando com gradiente `#FA094E → #940755` via `background-clip:text`.
- Cabeçalho: fundo branco, logo positivo 30 px, eyebrow em gradiente recortado ou cinza `#545353` em caixa alta, régua de 3 px em `--am-grad-rule` embaixo.
- Tabela: cabeçalho em caixa alta cinza, linhas com fio `#E3E3E1`, hover em `#FFF3F7`.
- Link: `#C9073F` sublinhado; hover `#FA094E`.

## Exemplos de uso errado

- `h2 { color:#44055A }` ou `header { background:#03045E }` — roxo/navy como cor dominante.
- `body { background:#100F0F }` ou faixa preta de 120 px no topo — "pesado".
- Série de gráfico em `#1E6FB8` / `#3B82F6` — azul, fora da paleta.
- `@media (prefers-color-scheme: dark)` — o arquivo abre escuro para quem revisa.
- `<link href="https://fonts.googleapis.com/...">` — dependência externa em arquivo aberto do disco.
- Texto de 13 px em `#FA094E` ou `#8A8A8F` — reprova contraste.
