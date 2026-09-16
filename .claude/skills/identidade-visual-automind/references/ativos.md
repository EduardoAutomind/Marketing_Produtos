# Ativos de `Id_visual/` — qual arquivo usar em cada situação

Caminhos relativos à raiz do repositório. Inventário conferido em 2026-09-16 (265 arquivos; a estrutura do briefing §8 bate com a pasta). Não editar nada em `Id_visual/`.

## Logotipo AutoMind — `Id_visual/_Marca/RGB/PNG/` (tela) e `RGB/PDF/` (vetor)

Todos os horizontais têm 1800 × 500 px, fundo transparente. Símbolos isolados 1000 × 1000 px. CMYK espelha a mesma lista em `_Marca/CMYK/` para impressão gráfica (não usar em tela).

| Situação | Arquivo |
|---|---|
| **Cabeçalho de HTML/PDF/dashboard** (fundo branco, ~30 px de altura) | `Horizontal - Positivo - Símbolo Preenchido Gradiente - Sem Tagline.png` |
| Capa de PDF / abertura de apresentação (marca grande, ≥ 60 px) | `Horizontal - Positivo - Símbolo Preenchido Gradiente - Com Tagline.png` |
| Alternativa leve sobre fundo claro | `Horizontal - Positivo - Símbolo Vazado Gradiente - Sem Tagline.png` |
| Impressão 1 cor / carimbo (fundo claro) | `Horizontal - Positivo - Símbolo Vazado - Sem Tagline.png` (preto) |
| Sobre fundo escuro `#100F0F` ou foto escurecida | `Horizontal - Negativo - Símbolo Preenchido Gradiente - Sem Tagline.png` |
| Bordado / serigrafia / 1 cor sobre escuro | `Horizontal - Negativo - Símbolo Vazado - Sem Tagline.png` (branco) |
| **Favicon, ícone, avatar, marca-d'água** | `Símbolo Preenchido Gradiente.png` (ou `Símbolo Vazado Gradiente.png`) |
| Símbolo mono | `Símbolo Vazado Positivo.png` (preto) / `Símbolo Vazado Negativo.png` (branco) |
| Tela de login / sistemas | `Login-250-138.png` (250 × 138 px, já no tamanho) |

Regra: fundo claro → Positivo; fundo escuro → Negativo; gradiente sempre que der; Sem Tagline quando pequeno. Área de proteção = altura do símbolo.

## Sub-marcas

| Produto | Pasta | Arquivos | Observação |
|---|---|---|---|
| AutoLoad | `Id_visual/Marca AutoLoad/` | `Versão Positivo.{png,svg}` (preto), `Versão Negativo.{png,svg}` (branco), `Versão Degradê.png` (roxo → magenta), `logo-autoload.ai` | 1920 × 592 px. Wordmark `autoload®` |
| AutoMed | `Id_visual/Marca AutoMed/` | `Versão Positivo.{png,svg}`, `Versão Negativo.{png,svg}`, `logo-automed.ai` | 1920 × 592 px. Wordmark `automed®`. Não há versão degradê |
| AutoChecker | — | — | **Não tem sub-marca própria.** Usa a marca AutoMind |

Os SVGs são leves (paths com fill único) — preferir SVG inline em HTML em vez de PNG base64. Quando a sub-marca é protagonista, a AutoMind entra como endossante, menor, no rodapé.

## Fontes — `Id_visual/Fontes/`

| Família | Pasta | Arquivos a embutir em HTML |
|---|---|---|
| **Hando** (principal, títulos) | `Fontes/Hando/` — 20 OTF (HairLine → Black + oblíquas) | `Hando-Bold.otf` (700, ~80 KB base64) e `Hando-Medium.otf` (500). Para capa/chamada: `Hando-ExtraBold.otf` (800) |
| **Red Hat Display** (secundária, corpo) | `Fontes/Red Hat Display/` — 14 TTF estáticos | `RedHatDisplay-Regular.ttf` (400), `-Medium.ttf` (500), `-Bold.ttf` (700), cada um ~61 KB base64. Itálico para a tagline: `-Italic.ttf` |
| Manrope (substituta da Hando) | `Fontes/Manrope/` — 7 TTF | Só quando Hando não puder ser embutida |
| Apoio | Bebas_Neue, Epilogue, Exo, Mollen, Oswald, Noto_Sans_Symbols, `Fontes.zip` | Peças específicas; nunca substituem as oficiais |

`@font-face` gerado por `scripts/embutir_ativos.py`; formato `opentype` para OTF e `truetype` para TTF, sempre com `font-display:swap`.

## Aplicações prontas

| Uso | Arquivo | Dimensão |
|---|---|---|
| Avatar redes sociais | `Id_visual/_Avatar/Fundo Branco + Símb. Gradiente.jpg` (padrão), `Fundo Preto + Símb. Gradiente.jpg`, `Fundo Preto + Marca Preenchida.jpg`, `Fundo Preto + Marca Vazada.jpg` | 1080 × 1080 |
| Capas | `Id_visual/_Capa/Facebook.jpg` 1980×730 · `Linkedin.jpg` 1536×220 · `Linkedin Pessoal.jpg` 792×191 · `Twitter.jpg` 1500×500 · `Youtube.jpg` 2560×1440 | — |
| Assinatura de e-mail | `Id_visual/Assinatura de E-mail/Assinatura-Email.jpg` | 320 × 200 |
| Wallpaper | `Id_visual/Wallpapers e BG/WALLPAPER.jpg`, `WALLPAPER2.jpg` | 1920 × 1080 |
| Fundo de reunião | `Id_visual/Wallpapers e BG/BG_REUNIÃO - Branco gelo - Opção 1.png` (fundo `#F3F3F0`, marca vazada positiva, `SIMPLE / SMART / RELIABLE`) | 1919 × 1081 |
| Modelo de proposta | `Id_visual/Propostas/Proposta Técnica V3.docx` | — |
| Ícones de contato (propostas, rodapés) | `Id_visual/Propostas/Ícones Sociais AutoMind/Ícones Pretos/` e `Ícones Brancos/` — `Email`, `Endereço`, `Instagram`, `Linkedin`, `Site`, `Telefone`.png | — |
| Adesivo de capacete | `Id_visual/Adesivo Capacete/Adesivo Capacete.{ai,pdf}` | produção |
| Uniforme | `Id_visual/Macacão/Versão 2/` (marca negativa vazada com/sem tagline + arte do macacão) | produção |
| Resumo oficial (logo, fontes, paleta) | `Id_visual/Resumo Identidade Visual AutoMind.png` | 2480 × 1990 |

## Fotografia

Universo industrial/logístico (caminhões, plataformas, painéis). Sempre em **preto e branco escurecido**, marca negativa por cima; a cor da peça vem só do gradiente do símbolo. Não colocar marca sobre foto colorida ou clara.
