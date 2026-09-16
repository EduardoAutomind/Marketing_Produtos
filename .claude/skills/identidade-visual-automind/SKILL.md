---
name: identidade-visual-automind
description: Aplica a identidade visual oficial da AutoMind (paleta, tipografia Hando/Red Hat Display, logotipo, tema claro fixo) em qualquer entregável — HTML, dashboard, relatório, PDF, XLSX, Markdown renderizado, apresentação, proposta. Use sempre que for criar, revisar ou ajustar um arquivo entregável da AutoMind, AutoChecker, AutoLoad ou AutoMed, ou quando o usuário mencionar identidade visual, marca, paleta, cores, fontes, logo, "deixar no padrão AutoMind", "aplicar a identidade", "brand", "clean", "tema claro".
---

# Identidade visual AutoMind em entregáveis

Fonte de verdade: `Id_visual/Identidade Visual AutoMind.md` (briefing) e `Id_visual/Resumo Identidade Visual AutoMind.png`. Esta skill condensa o briefing em regras operacionais, tokens prontos e scripts. Em caso de conflito, o briefing vence — e avise o usuário.

## Fluxo

1. **Identifique o formato** do entregável (HTML/dashboard, PDF via Edge headless, XLSX, Markdown→HTML, DOCX/PPTX, imagem) e o **produto** (AutoMind, AutoChecker, AutoLoad, AutoMed) — define qual logotipo entra.
2. **Comece pelos tokens**: copie `references/tokens.css` para o `<style>` (HTML) ou use as constantes de `references/paleta.md` (Python/openpyxl/reportlab). Não invente hex fora da paleta.
3. **Embuta fontes e logo** com `scripts/embutir_ativos.py` (gera `@font-face` em base64 e `<img>` data-URI a partir de `Id_visual/`). Entregáveis são abertos direto do disco/OneDrive: **zero dependência externa**.
4. **Escreva o conteúdo** seguindo as regras abaixo.
5. **Verifique** com `python .claude/skills/identidade-visual-automind/scripts/verificar_entregavel.py <arquivo.html>` e corrija tudo que ele apontar antes de entregar.
6. Ao entregar, percorra o checklist do final.

## Regras inegociáveis

### Tema claro por padrão
- `:root { color-scheme: light }`, `body { background:#FFFFFF; color:#100F0F }`.
- **Proibido** `@media (prefers-color-scheme: dark)` e qualquer detecção automática do tema do sistema. O arquivo abre branco mesmo em sistema em modo escuro. Motivo: a liderança revisa em modo escuro e já devolveu entregáveis que abriram escuros.
- **Modo noturno só como opt-in manual** (quando pedido): botão no cabeçalho, `data-theme="dark"` no `<html>`, escolha guardada em `localStorage` e aplicada antes da pintura; nunca lida de `prefers-color-scheme`. Impressão sempre clara. No escuro, seguir o briefing: fundo `#100F0F`, logotipo **Negativo**, texto `#F3F3F0`, neutros = gelo diluído no preto (`#181717` papel, `#2F2E2E` linha, `#BDBDBB` texto secundário), rosa chapado/`--grad-realce` no lugar do gradiente completo (a metade navy some sobre preto), HT `#C9C9C6` (o `#3F3F45` some), status clareados. Receita pronta em `Marketing/Py/_dashboard_marketing_src.html` (bloco `:root[data-theme="dark"]`).

### Cor — leitura "branco + cinza + rosa leve"
- Fundo branco `#FFFFFF` (ou gelo `#F3F3F0` em áreas de apoio). **Neutros derivados da paleta** (preto diluído no gelo): texto secundário `#545353`, terciário `#6F6F6E`, borda `#E3E3E1`, borda forte `#D3D3D0`, fundo de cartão `#FBFBFA`. Nenhum cinza inventado.
- **Rosa cheio `#FA094E` só como acento**: métrica prioritária, série DT, botão principal, régua em gradiente. Nunca em grandes áreas.
- **Rosa em texto pequeno usa `#C9073F`** (`--rosa-text`): o `#FA094E` sobre branco dá 4,0:1 e reprova AA abaixo de 18 px. Lavagens `#FFEEF3` / `#FFF3F7` para fundos de destaque.
- **Roxo `#44055A` e navy `#03045E` não são cor de título nem de fundo.** Títulos em preto `#100F0F`. Roxo/navy só dentro do gradiente (símbolo, régua fina) ou em detalhe pontual.
- **Sem faixas escuras grandes no cabeçalho.** Cabeçalho de marca = fundo branco, logo positivo, régua de 3 px em gradiente embaixo.
- Gráficos: **DT `#FA094E` / HT `#3F3F45`** (par validado para daltonismo). **Nunca azul** como série de dados. Rampa ordinal (funil, intensidade) em rosa: `#FBD9E3 → #F4A0BB → #EC5C88 → #C8104A`.
- Semântica de status (única exceção de cor fora da paleta, e só em pílulas/badges pequenos): ok `#0F8A5F`/`#E8F3EE`, atenção `#A86300`/`#FBF1DC`, crítico `#C31035`/`#FDE8EC`. Callouts do pipeline Md→HTML: `ℹ️` info usa lavagem rosa (não azul), `✅` ok verde, `⚠️` warn âmbar, `❌` bad vermelho.

### Gradiente
- **Do símbolo** (nunca redesenhar; usar o PNG/PDF oficial): `linear-gradient(45deg,#03045E 0%,#44055A 33%,#940755 66%,#FA094E 100%)`.
- **Em HTML, sempre 2 stops** `#FA094E → #03045E` (45° em botão/texto recortado, 90° em régua, 180° em barra lateral). Magenta e roxo são a interpolação, não paradas. Só em acento: régua ≤ 4 px, barra de 4 px em cartão, botão principal, eyebrow/número-herói com `background-clip:text`. Não em fundos inteiros nem texto corrido.
- Ondas de cronograma (7 tons): `FA094E → CF1A66 → 940755 → 6F1170 → 44055A → 231A66 → 03045E`.

### Tipografia
- **Hando** (títulos, KPIs, números grandes) — pesos 700 (Bold) e 500 (Medium); em chamadas curtas pode ir a 800/900.
- **Red Hat Display** (corpo, tabelas, rótulos) — 400 corpo, 500 rótulos, 700 destaques.
- Stacks: títulos `"Hando","Manrope","Red Hat Display","Segoe UI",Arial,sans-serif`; texto `"Red Hat Display","Segoe UI",system-ui,Arial,sans-serif`.
- Em HTML autocontido, embutir Hando 700/500 e Red Hat Display 400/500/700 em base64 (~340 KB no total). Não linkar Google Fonts.
- Títulos sempre `#100F0F`. Caixa alta com tracking aberto (`letter-spacing:.1em`–`.18em`) é permitida em rótulos curtos e ecoa o logotipo. Nada de serifa, decorativa ou manuscrita.

### Logotipo
- Fundo claro → **Positivo**; fundo escuro → **Negativo**. Símbolo em gradiente sempre que possível; mono só por limitação técnica.
- Cabeçalho de HTML/PDF: `_Marca/RGB/PNG/Horizontal - Positivo - Símbolo Preenchido Gradiente - Sem Tagline.png` a ~30 px de altura. Com Tagline só quando a marca aparece grande (capa, ≥ 60 px). Ícone/favicon: `Símbolo Preenchido Gradiente.png`.
- Área de proteção = altura do símbolo. Nunca distorcer, recolorir, aplicar sombra/contorno, nem recompor "AUTOMIND" com fonte (o "D" aberto é parte da marca).
- Tagline escrita exatamente `Simple · Smart · Reliable` (ponto mediano, itálico quando acompanha o logo).
- **Sub-marcas** (AutoLoad, AutoMed): wordmark em minúsculas com `®`; em `Id_visual/Marca AutoLoad/` e `Marca AutoMed/` (SVG positivo = preto, negativo = branco). Quando a sub-marca é protagonista, a AutoMind entra menor (rodapé) como endossante — nunca as duas do mesmo tamanho lado a lado. AutoChecker não tem sub-marca própria: usa a marca AutoMind.

### Forma (padrão consolidado na LP Expopostos 2026)
- **Cantos retos**: nenhum `border-radius` em cartão, botão, chip, pílula ou campo.
- **Sem emoji** em interface; ícones só em SVG inline monocromático. Status por cor + texto.
- Eyebrow de seção em Hando, caixa alta, tracking `.22em`, **gradiente recortado**; título logo abaixo em Hando 800 com `letter-spacing:-.03em`.
- Botão principal com fundo em gradiente e sombra em rosa (`rgba(250,9,78,.28)`); secundário branco com borda `#D3D3D0`. Sombras de cartão sempre em roxo (`rgba(68,5,90,.12)`), nunca cinza.
- Marcadores de lista: quadrado de 8 px em gradiente (`li::before`).
- Dashboards: cabeçalho fixo compacto (logo + título + status à direita), abas fixas por view, seções com cabeçalho + controles à direita. Referência: `Marketing/Py/_dashboard_marketing_src.html`.

### Por formato
- **HTML/dashboard**: single-file, CSS inline, fontes+logo em base64, `color-scheme:light`, largura máxima 1080–1180 px, gutter 16 px no celular, sem scroll horizontal. Cartões `#FBFBFA` com borda `#E3E3E1`, cantos retos; cartão prioritário com barra de 4 px em gradiente no topo, borda `#F9C6D6` e fundo `#FFF3F7→#FFFFFF`.
- **PDF**: gerado do HTML com `msedge --headless --disable-gpu --no-pdf-header-footer --print-to-pdf`. Adicione `@page { size:A4; margin:14mm }` e `@media print` que preserve cores (`-webkit-print-color-adjust:exact; print-color-adjust:exact`). Cabeçalho branco com logo, rodapé cinza `#545353` com produto · data.
- **XLSX (cronogramas)**: seguir `AutoMed/_gerar_xlsx_cronograma_automed.py` (coluna `#` por onda, fills P/M/G, aba Legenda). A capa navy desse modelo é **exceção herdada** — mantida para consistência entre os três cronogramas, não replicar em planilhas novas de outro tipo (capa branca + régua rosa).
- **Markdown**: a fonte é neutra; a identidade entra no gerador HTML. Callouts por emoji (`⚠️ ❌ ✅ ℹ️`) como no pipeline existente.
- **DOCX/PPTX**: partir de `Id_visual/Propostas/Proposta Técnica V3.docx`; ícones de contato em `Propostas/Ícones Sociais AutoMind/`.
- **Imagem/social**: templates em `_Avatar/`, `_Capa/`; foto sempre P&B escurecida, marca negativa, a cor vem só do gradiente do símbolo.

## Referências desta skill
- `references/tokens.css` — `:root` completo + base (body, títulos, cabeçalho de marca, cards, callouts, print). Copiar e colar.
- `references/paleta.md` — tabela de cores com papel, contraste medido e constantes Python.
- `references/esqueleto.html` — página mínima com placeholders `{{FONTES}}`, `{{TOKENS}}`, `{{LOGO}}` para começar um entregável.
- `references/ativos.md` — qual arquivo de `Id_visual/` usar em cada situação, com caminho exato.
- `scripts/embutir_ativos.py` — gera `@font-face` e `<img>` em base64; também importável.
- `scripts/verificar_entregavel.py` — lint de um HTML contra estas regras (tema, fontes, cores fora da paleta, roxo/navy em título, dependências externas).

## Checklist de entrega
- [ ] Abre branco em sistema em modo escuro (`color-scheme:light`, sem `prefers-color-scheme`)? Se há modo noturno, é manual, padrão claro, logo Negativo e rosa chapado?
- [ ] Logo correto para o fundo, em gradiente, com área de proteção, sem tagline quando pequeno?
- [ ] Títulos em Hando preto; corpo em Red Hat Display; fontes embutidas, nenhuma URL externa?
- [ ] Rosa cheio só como acento; texto rosa em `#C9073F`; nenhum título/fundo roxo ou navy; nenhuma faixa preta grande?
- [ ] Séries DT rosa / HT cinza-chumbo, sem azul?
- [ ] Tagline `Simple · Smart · Reliable`; sub-marca com `®` e AutoMind como endossante?
- [ ] `verificar_entregavel.py` sem erros?
- [ ] Nome do arquivo `<Assunto>_<Produto>_<AAAA-MM-DD>.<ext>` e conteúdo em português do Brasil?
