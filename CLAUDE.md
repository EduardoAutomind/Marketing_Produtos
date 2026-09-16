# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## O que é este repositório

Repositório de **entregáveis internos da AutoMind** (produtos AutoChecker, AutoLoad V4, AutoMed e o setor de Marketing): estudos, auditorias, cronogramas, dashboards e ativos de marca. **Não é um projeto de software** — não há build, lint ou suíte de testes. O "código" existente são scripts Python descartáveis que geram HTML/PDF/XLSX a partir de Markdown.

Todo o conteúdo (documentos, comentários, nomes de arquivo, mensagens ao usuário) é escrito em **português do Brasil**.

## Estrutura

Cada produto tem sua pasta na raiz, com subpastas por formato:

```
<Produto>/
  Md/    fonte canônica de cada documento (.md)
  Html/  versão renderizada para leitura/compartilhamento
  Pdf/   versão impressa (gerada a partir do HTML)
  Py/    scripts geradores (prefixo `_`, ex.: _gerar_pdfs_2026-07-21.py)
```

- `AutoChecker/` — o produto com mais material: cronograma de observabilidade (ondas 0–4, etapas 1–8), auditorias LGPD/PII, estudos de uso da Base Compartilhada, dashboard Grafana (`Grafana/`) e YAMLs de pipeline do Azure DevOps (`_azdo_yaml/`).
- `AutoLoad/` e `AutoMed/` — mesma lógica, menos volume. `AutoMed/` não usa subpastas Md/Html/Pdf.
- `Marketing/` — dashboard de marketing (protótipo HTML autocontido) e o `.md` de contexto com glossário (HT/DT, funil, ABM) e a estrutura proposta. **Trabalho em andamento nesta branch.**
- `Id_visual/` — identidade visual oficial da AutoMind (logos, fontes, wallpapers, ícones). Fonte de verdade para cores e tipografia; não editar.

Documentação técnica de referência de cada produto: `AutoChecker/Md/AutoChecker-documentacao.md`, `AutoLoad/Md/Autoload_V4-documentacao.md`, `AutoMed/Contexto_Observabilidade_Automed_2026-06-08.md`. Consulte-as antes de escrever qualquer coisa sobre arquitetura, Sentry (org `automind-qd`) ou tenants.

## Convenções de nomenclatura

`<Assunto>_<Produto>_<AAAA-MM-DD>.<ext>` — mesmo slug em `Md/`, `Html/` e `Pdf/` para o mesmo documento (ex.: `Estudo_Uso_por_Cliente_AutoChecker_2026-07-10.{md,html,pdf}`). A data é a de elaboração; um documento revisado ganha novo arquivo com nova data, não sobrescreve o anterior. Scripts geradores começam com `_`.

## Pipeline Markdown → HTML → PDF

Padrão usado em todos os geradores (`*/Py/_gerar_*.py`):

1. O `.md` em `Md/` é a fonte canônica; o HTML é renderizado com a lib `markdown` (extensões `tables`, `fenced_code`, `sane_lists`, `toc`, `attr_list`).
2. Blockquotes iniciados por emoji viram callouts coloridos: `⚠️`=warn, `❌`=bad, `✅`=ok, `ℹ️`=info.
3. O PDF é impresso do HTML via **Edge/Chrome headless**: `msedge --headless --disable-gpu --no-pdf-header-footer --print-to-pdf=<saída> <file:///url>` (candidatos em `C:\Program Files*\Microsoft\Edge\Application\msedge.exe`).
4. HTML é **autocontido**: CSS inline, fontes embutidas em base64 quando necessário, sem dependências externas — os arquivos são abertos direto do disco/OneDrive.

Dependências Python (instalar sob demanda, não há requirements.txt): `markdown`, `openpyxl` (cronogramas .xlsx), `reportlab` (só em `_gen_auditoria_onda0.py`).

Rodar um gerador: `python AutoChecker/Py/_gerar_detalhamento_html.py --md ... --tpl ... --out ...` (ver docstring de cada script; a maioria não recebe argumentos e usa caminhos relativos a `Path(__file__)`).

Atenção: alguns scripts antigos têm caminhos absolutos para `C:\Projetos\Observabilidade` e importam um `_obs_lib/pdf.py` que **não está neste repositório** (`_gerar_pdfs_2026-07-21.py`, `_gen_auditoria_onda0.py`). Eles não rodam aqui sem ajuste; ao criar um novo gerador, use caminhos relativos ao próprio arquivo, como fazem `_gerar_explicacao_html_pdf.py` e `_gerar_pdf_cronograma_automed.py`.

## Identidade visual (obrigatória em HTML/PDF/XLSX)

**Use a skill `identidade-visual-automind`** (`.claude/skills/identidade-visual-automind/`) ao criar ou revisar qualquer entregável: ela tem os tokens CSS prontos, o mapa de ativos de `Id_visual/`, o script que embute fontes/logo em base64 e o verificador `scripts/verificar_entregavel.py <arquivo.html>`, que deve passar sem erros antes da entrega. Briefing completo: `Id_visual/Identidade Visual AutoMind.md`. O resumo abaixo é o mínimo.

Paleta oficial (`Id_visual/Resumo Identidade Visual AutoMind.png`):

| Cor | Hex | Uso típico |
|---|---|---|
| Rosa | `#FA094E` | acento principal, início do gradiente |
| Magenta | `#940755` | intermediário |
| Roxo | `#44055A` | títulos de seção, capa |
| Navy | `#03045E` | fim do gradiente |
| Preto | `#100F0F` | texto/fundo escuro |
| Branco gelo | `#F3F3F0` | fundo claro |

Gradiente da marca: rosa → navy (`linear-gradient(90deg,#FA094E,#03045E)`). Ondas de cronograma usam a progressão `FA094E → CF1A66 → 940755 → 6F1170 → 44055A → 231A66 → 03045E`.

**Leitura clara obrigatória em HTML novo:** abre branco por padrão (`color-scheme:light`, nunca `prefers-color-scheme: dark`; modo noturno só como botão opt-in com padrão claro), cinzas neutros, rosa em lavagens claras (`#FFEEF3`, `#FFF3F7`) nos destaques e rosa cheio só como acento. Não usar roxo/navy como cor dominante nem faixas pretas grandes no cabeçalho. Séries de dados: DT `#FA094E` / HT `#3F3F45` (par validado para daltonismo). Motivo: quem revisa usa o sistema em modo escuro e quer que o entregável abra branco.

Fontes: **Hando** (principal, títulos) e **Red Hat Display** (secundária, corpo); arquivos em `Id_visual/Fontes/`. Nos HTML autocontidos a Red Hat Display é embutida em base64 com fallback `"Segoe UI", system-ui`.

Os cronogramas `.xlsx` (AutoChecker/AutoLoad/AutoMed) compartilham o mesmo modelo: capa navy, coluna `#` colorida por onda, fills de esforço P/M/G (`DBEAFE`/`FEF9C3`/`FED7AA`), fills de status com dropdown, aba Legenda. Ao criar um novo, copie `AutoMed/_gerar_xlsx_cronograma_automed.py`.

## Dashboard de Marketing (`Marketing/Html/Dashboard_Marketing_AutoMind_2026-09-16.html`)

Protótipo single-file (~480 KB, boa parte é fonte base64) **gerado** por `Marketing/Py/_gerar_dashboard_marketing.py` a partir do template `Marketing/Py/_dashboard_marketing_src.html` (fonte canônica — edite o template, não o HTML). O gerador embute Hando/Red Hat Display e o logo via a skill `identidade-visual-automind`. Rodar: `python Marketing/Py/_gerar_dashboard_marketing.py --data AAAA-MM-DD`.

Organização (herdada do dashboard de observabilidade Sentry, layout da LP Expopostos 2026):

- **Cabeçalho fixo**: logo + título, à direita o seletor de mês segmentado (`#periodo`), comparação com o mês anterior, pílulas de status ("Ilustrativo", "2.5 s/ rastreio"), menu **Exportar** (CSV / Markdown / JSON do mês) e ajuda `?`.
- **Abas fixas** (`.aba[data-view]`) = views: `geral` (banner de status, KPIs, cartões por frente DT/HT/Funil, destaque), `producao`, `performance` (busca, chips DT/HT, ordenação na tabela de indicador-chave), `funil` (métrica 2.5 + histórico), `pendencias`. Rota por `#hash`; atalhos `1`–`5`, `[`/`]` mudam o mês, `e` exporta, `/` busca, `?` ajuda.
- Bloco `DADOS` no final do `<script>`: objeto mês → `{producao, perf, acessos, funil, destaque}` com **dados ilustrativos**. É o único ponto a editar para trocar números; `MESES` e `CATS` (com trilha `dt`/`ht`) derivam dele.
- Funil segue as etapas do glossário: cadastros de trial vindos do DT → testaram → consideration → assinatura. A métrica prioritária (definida pela liderança) é **cadastros de trial vindos do DT e quantos de fato testaram**.
- `localStorage` (wrapper `LS` com try/catch) persiste mês, view, "destaque do mês" e checkboxes de pendências por navegador.
- Abre sempre em tema claro (`color-scheme:light`); **modo noturno** é opt-in pelo botão do cabeçalho (`t`), guardado em `localStorage`, nunca por `prefers-color-scheme`. No escuro: fundo `#100F0F`, logo Negativo, tokens semânticos (`--fundo`, `--ink`, `--papel`…) redefinidos em `:root[data-theme="dark"]`. Cantos retos, gradiente de 2 stops, sem emoji — `verificar_entregavel.py` deve passar sem erros.

O contexto de negócio, glossário e pendências a cobrir (webinars, ações de comunidade) estão em `Marketing/Dashboard_Marketing_Contexto_2026-09-15.md` — leia antes de alterar o dashboard.

## Git

- Branch principal: `master`. Trabalho em branches `EduardoAutomind/<tema>`; remote `origin` no GitHub (`EduardoAutomind/Marketing_Produtos`).
- Ativos binários (PDF, XLSX, PNG, fontes, `.ai`) são versionados diretamente; não há LFS.
- `AutoChecker/Html/Política de Privacidade _ AutoChecker*` e `Termo de Uso _ AutoChecker*` são capturas "salvar página completa" do site público (Next.js) — referência, não editar.
