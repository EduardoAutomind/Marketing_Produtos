# Identidade Visual AutoMind — Padrões e Regras

> Documento de referência para qualquer material da AutoMind: apresentações, propostas, dashboards, relatórios HTML, redes sociais, uniformes e sinalização.
> Fonte primária: `Resumo Identidade Visual AutoMind.png` e os arquivos de marca desta pasta (`Id_visual`).

---

## 1. Essência da marca

| Item | Definição |
|---|---|
| Nome | **AutoMind** (grafado `AUTOMIND` no logotipo, em caixa alta) |
| Tagline | **Simple · Smart · Reliable** |
| Personalidade | Simples, inteligente e confiável — tecnologia industrial com visual limpo e direto |
| Universo de imagem | Indústria, logística e engenharia: caminhões, plataformas, painéis de instrumentação (ver `Wallpapers e BG/`) |

A tagline é sempre escrita em inglês, com as três palavras separadas por ponto mediano (`·`) e em itálico quando acompanha o logotipo. Em peças de destaque (ex.: fundo de reunião) pode aparecer em caixa alta, empilhada, em peso extra-bold: `SIMPLE / SMART / RELIABLE`.

---

## 2. Logotipo

### 2.1 Elementos

1. **Símbolo** — dois "A"/"M" sobrepostos formando uma montanha dupla. Existe em duas construções:
   - **Preenchido** (sólido, sempre em gradiente da marca);
   - **Vazado** (apenas contorno/traço; pode ser em gradiente, preto ou branco).
2. **Logotipo** — a palavra `AUTOMIND` em caixa alta, geométrica, com o "D" final aberto (traço característico da marca — nunca substituir por uma fonte comum).
3. **Tagline** — `Simple · Smart · Reliable`, alinhada à direita sob o logotipo.

### 2.2 Versões oficiais

Todas as versões estão em `_Marca/RGB/` (tela) e `_Marca/CMYK/` (impressão), nos formatos PDF (vetor) e PNG (fundo transparente).

| Versão | Quando usar |
|---|---|
| Horizontal · Positivo · Símbolo Preenchido Gradiente | Versão principal sobre fundos claros |
| Horizontal · Positivo · Símbolo Vazado Gradiente | Alternativa mais leve sobre fundos claros |
| Horizontal · Positivo · Símbolo Vazado (preto) | Monocromática sobre fundo claro; carimbo, gravação, impressão 1 cor |
| Horizontal · Negativo · Símbolo Preenchido Gradiente | Versão principal sobre fundos escuros (`#100F0F`) e fotos escurecidas |
| Horizontal · Negativo · Símbolo Vazado Gradiente | Alternativa sobre fundos escuros |
| Horizontal · Negativo · Símbolo Vazado (branco) | Monocromática sobre fundo escuro; uniformes, bordado, serigrafia |
| Símbolo isolado (Preenchido Gradiente / Vazado Gradiente / Vazado Positivo / Vazado Negativo) | Avatar, favicon, ícone de app, adesivo, marca-d'água |

Cada versão horizontal existe **Com Tagline** e **Sem Tagline**.

**Regra de escolha:**
- Fundo branco ou claro → versão **Positivo** (texto preto).
- Fundo preto, escuro ou fotografia escurecida → versão **Negativo** (texto branco).
- O símbolo em gradiente é sempre preferível; use as versões mono (preto/branco) só quando o gradiente não puder ser reproduzido.
- Use **Sem Tagline** quando a marca for aplicada pequena (a tagline deixa de ser legível) ou quando a tagline já aparece em outro ponto da peça.

### 2.3 Regras de aplicação

- **Área de proteção:** manter ao redor da marca uma margem livre equivalente à altura do símbolo. Nada de textos, bordas ou outros elementos dentro dessa área.
- **Tamanho mínimo:** a versão horizontal com tagline não deve ser reduzida a ponto de a tagline ficar ilegível — abaixo disso use a versão sem tagline; para tamanhos muito pequenos (ícone, favicon) use apenas o símbolo. Arquivo de referência para login/sistemas: `_Marca/RGB/PNG/Login-250-138.png` (250 × 138 px).
- **Proibições:**
  - Não distorcer, inclinar, rotacionar ou espelhar.
  - Não trocar as cores do gradiente nem aplicar cores fora da paleta.
  - Não recompor o logotipo com outra fonte (o "D" aberto é parte da marca).
  - Não aplicar sombras, contornos extras, brilhos ou efeitos 3D.
  - Não colocar a versão Positivo sobre fundo escuro nem a Negativo sobre fundo claro.
  - Não aplicar sobre fotos sem escurecê-las/clareá-las o suficiente para garantir contraste (ver padrão dos wallpapers: foto em preto e branco escurecida).

---

## 3. Cores

### 3.1 Paleta oficial

| Nome | HEX | RGB | Papel |
|---|---|---|---|
| Rosa AutoMind (primária) | `#FA094E` | 250, 9, 78 | Cor principal de destaque; extremidade clara do gradiente |
| Magenta | `#940755` | 148, 7, 85 | Tom intermediário do gradiente |
| Roxo | `#44055A` | 68, 5, 90 | Tom intermediário do gradiente |
| Navy | `#03045E` | 3, 4, 94 | Extremidade escura do gradiente |
| Preto AutoMind | `#100F0F` | 16, 15, 15 | Texto, logotipo positivo, fundos escuros |
| Branco Gelo | `#F3F3F0` | 243, 243, 240 | Fundo claro oficial (usado no fundo de reunião) |

Para impressão, utilize os arquivos já convertidos em `_Marca/CMYK/` em vez de converter os HEX manualmente.

### 3.2 Gradiente da marca

O gradiente do símbolo percorre a paleta do **navy ao rosa**:

```
#03045E → #44055A → #940755 → #FA094E
```

- No símbolo **preenchido**: cada "perna" recebe o gradiente com o rosa no topo/direita e o navy na base/esquerda, criando o efeito de sobreposição entre as duas formas.
- No símbolo **vazado**: o gradiente corre ao longo do traço, do navy (base esquerda) ao rosa (topo direito).
- O gradiente é exclusivo do símbolo. Não aplicar em textos, fundos inteiros ou botões.

CSS de referência:

```css
background: linear-gradient(45deg, #03045E 0%, #44055A 33%, #940755 66%, #FA094E 100%);
```

### 3.3 Tons de apoio (derivados, para interfaces e dashboards)

| Nome | HEX | Uso |
|---|---|---|
| Rosa lavado 1 | `#FFEEF3` | Fundo de cards/blocos de destaque |
| Rosa lavado 2 | `#FFF3F7` | Fundo de linhas/áreas em realce leve |
| Cinza-chumbo | `#3F3F45` | Série secundária em gráficos, texto de apoio |
| Cinza neutro claro | `#E5E5E3` | Bordas, divisores |
| Cinza médio | `#8A8A8F` | Texto secundário, legendas |

### 3.4 Regras de uso da cor

1. **Base clara.** A leitura da identidade em materiais de trabalho (dashboards, relatórios, modelos HTML) é **branco + cinzas neutros + rosa em tons leves**. O fundo é branco (`#FFFFFF`) ou branco gelo (`#F3F3F0`).
2. **Rosa cheio (`#FA094E`) só como acento**: métrica prioritária, botão principal, série de dados em destaque, régua/linha em gradiente. Nunca como cor dominante de grandes áreas.
3. **Roxo e navy não são cores de título nem de fundo.** Aparecem apenas dentro do gradiente do símbolo (ou em detalhes muito pontuais). Títulos são em preto `#100F0F`.
4. **Faixas escuras grandes (`#100F0F`) em cabeçalhos** são evitadas em materiais de uso corrente — resultam pesadas. O preto fica reservado ao texto e às peças institucionais/fotográficas (wallpaper, assinatura de e-mail, avatar).
5. **Gráficos e séries de dados:** par validado **DT rosa `#FA094E` / HT cinza-chumbo `#3F3F45`**. Não usar azul como série de dados.
6. **Entregáveis HTML têm tema claro fixo:** declarar `color-scheme: light` no `:root`, pintar todas as cores explicitamente e **não** usar `@media (prefers-color-scheme: dark)` nem blocos `[data-theme="dark"]`. O material deve abrir branco mesmo em sistemas em modo escuro.

Tokens CSS de referência:

```css
:root {
  color-scheme: light;
  --am-pink: #FA094E;
  --am-magenta: #940755;
  --am-purple: #44055A;
  --am-navy: #03045E;
  --am-black: #100F0F;
  --am-ice: #F3F3F0;
  --am-white: #FFFFFF;
  --am-pink-wash-1: #FFEEF3;
  --am-pink-wash-2: #FFF3F7;
  --am-gray-dark: #3F3F45;
  --am-gray-mid: #8A8A8F;
  --am-gray-line: #E5E5E3;
}
body { background: var(--am-white); color: var(--am-black); }
```

---

## 4. Tipografia

### 4.1 Famílias oficiais

| Papel | Fonte | Pasta | Observações |
|---|---|---|---|
| **Principal** | **Hando** | `Fontes/Hando/` (OTF, Hairline → Black, com oblíquas) | Títulos, destaques, chamadas. Geométrica, combina com o logotipo. Usar pesos Bold / ExtraBold / Black em títulos. |
| **Secundária** | **Red Hat Display** | `Fontes/Red Hat Display/` | Textos corridos, subtítulos, interfaces, tabelas. Pesos Regular / Medium para corpo; SemiBold para rótulos. |

A tagline (`Simple · Smart · Reliable`) é composta em itálico na fonte secundária. Sempre que houver o arquivo vetorial oficial da marca com tagline, use-o em vez de redigitar.

### 4.2 Fontes de apoio disponíveis

Também estão na pasta `Fontes/` e podem ser usadas em peças específicas, sem substituir as oficiais: Bebas Neue, Epilogue, Exo, Manrope, Mollen (com variações Condensed/Narrow), Oswald e Noto Sans Symbols (símbolos/ícones tipográficos). O `Fontes.zip` contém o pacote completo para instalação.

### 4.3 Substituição quando as fontes não puderem ser instaladas

- Hando → **Manrope** ou **Red Hat Display Bold** (ambas no Google Fonts).
- Red Hat Display → disponível no Google Fonts; fallback do sistema: `Segoe UI`, `Helvetica Neue`, `Arial`, sans-serif.

```css
font-family: "Hando", "Manrope", "Red Hat Display", "Segoe UI", Arial, sans-serif;   /* títulos */
font-family: "Red Hat Display", "Segoe UI", Arial, sans-serif;                        /* texto */
```

### 4.4 Regras tipográficas

- Títulos em **preto `#100F0F`**, nunca em roxo ou navy.
- Hierarquia enxuta: um peso forte para títulos, um regular para texto, um médio para rótulos/legendas.
- Caixa alta com tracking aberto é permitida em títulos curtos e chamadas (ecoa o logotipo `AUTOMIND`).
- Não usar fontes serifadas, decorativas ou manuscritas.

---

## 5. Sub-marcas de produto

| Produto | Arquivos | Descrição |
|---|---|---|
| **AutoLoad** | `Marca AutoLoad/` — `Versão Positivo`, `Versão Negativo` (PNG/SVG), `Versão Degradê` (PNG), `logo-autoload.ai` | Símbolo em espiral (letra "a" estilizada) + wordmark `autoload®` em minúsculas, geométrica e fina. A versão Degradê usa o gradiente roxo → magenta (`#44055A → #940755`). |
| **AutoMed** | `Marca AutoMed/` — `Versão Positivo`, `Versão Negativo` (PNG/SVG), `logo-automed.ai` | Símbolo de seta diagonal em quadrado (saída/crescimento) + wordmark `automed®` em minúsculas, mesma família tipográfica da AutoLoad. |

Regras:
- As sub-marcas seguem a mesma paleta e as mesmas regras de positivo/negativo da marca-mãe.
- Wordmark sempre em minúsculas, com o `®`.
- Quando a sub-marca aparece junto da AutoMind, a AutoMind é a marca endossante (menor ou em rodapé) e a sub-marca é a protagonista da peça — nunca as duas no mesmo tamanho lado a lado.

---

## 6. Aplicações padronizadas

| Aplicação | Pasta | Padrão |
|---|---|---|
| Avatar (redes sociais / perfis) | `_Avatar/` | Quatro opções: fundo branco + símbolo gradiente; fundo preto + símbolo gradiente; fundo preto + marca preenchida; fundo preto + marca vazada. Formato quadrado, marca centralizada com boa margem. |
| Capas de redes sociais | `_Capa/` | Facebook, LinkedIn (empresa e pessoal), Twitter/X e YouTube já nas dimensões de cada rede. |
| Assinatura de e-mail | `Assinatura de E-mail/Assinatura-Email.jpg` | Logotipo negativo com tagline sobre mosaico fotográfico escurecido (caminhão / plataforma / painel). |
| Wallpaper | `Wallpapers e BG/WALLPAPER.jpg`, `WALLPAPER2.jpg` | Mosaico fotográfico P&B escurecido, marca negativa no canto superior direito. |
| Fundo de reunião | `Wallpapers e BG/BG_REUNIÃO - Branco gelo - Opção 1.png` | Fundo `#F3F3F0`, marca positiva vazada sem tagline no canto superior esquerdo, `SIMPLE / SMART / RELIABLE` em caixa alta extra-bold à direita. |
| Adesivo de capacete | `Adesivo Capacete/` | Arquivo `.ai` e `.pdf` prontos para produção. |
| Macacão / uniforme | `Macacão/Versão 2/` | Marca negativa vazada (com e sem tagline) para aplicação em tecido escuro. |
| Propostas | `Propostas/` | Modelo `Proposta Técnica V3.docx` e ícones de contato (e-mail, endereço, Instagram, LinkedIn, site, telefone) em preto e em branco. |

Padrão de fotografia: imagens do universo industrial/logístico, tratadas em **preto e branco e escurecidas** para receber a marca em negativo — a cor da peça vem apenas do gradiente do símbolo.

---

## 7. Checklist rápido

Antes de publicar qualquer material, confira:

- [ ] A versão do logotipo está correta para o fundo (Positivo em claro, Negativo em escuro)?
- [ ] O símbolo está em gradiente (ou mono apenas por limitação técnica)?
- [ ] Área de proteção respeitada e proporções intactas?
- [ ] Títulos em Hando (ou substituta) e texto em Red Hat Display?
- [ ] Fundo branco/branco gelo, cinzas neutros e rosa só como acento?
- [ ] Nenhum título ou fundo em roxo/navy; nenhuma faixa escura grande no cabeçalho?
- [ ] Em HTML: `color-scheme: light`, sem adaptação a modo escuro?
- [ ] Gráficos com o par rosa `#FA094E` / cinza-chumbo `#3F3F45`, sem azul?
- [ ] Tagline escrita como `Simple · Smart · Reliable`?

---

## 8. Estrutura dos arquivos

```
Id_visual/
├── Resumo Identidade Visual AutoMind.png   ← resumo oficial (logo, fontes, paleta)
├── _Marca/
│   ├── RGB/  (PDF + PNG)                   ← uso em tela
│   └── CMYK/ (PDF + PNG)                   ← uso em impressão
├── _Avatar/                                ← perfis de redes sociais
├── _Capa/                                  ← capas de redes sociais
├── Fontes/                                 ← Hando, Red Hat Display e fontes de apoio
├── Marca AutoLoad/                         ← sub-marca
├── Marca AutoMed/                          ← sub-marca
├── Assinatura de E-mail/
├── Wallpapers e BG/
├── Adesivo Capacete/
├── Macacão/
└── Propostas/                              ← modelo de proposta e ícones de contato
```
