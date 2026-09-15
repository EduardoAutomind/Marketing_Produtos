# Dashboard Grafana — Uso por Cliente (Base Compartilhada)

Arquivo: `dashboard_uso_por_cliente_base_compartilhada.json`

O token do Grafana usado pela integração (MCP) é **somente-leitura**, então o dashboard
não pôde ser criado automaticamente (HTTP 403 — falta `dashboards:create/write`).
Segue pronto para importar manualmente por quem tiver permissão de edição.

## Como importar (2 minutos)

1. Acesse `https://monitor.autochecker.cloud` logado com um usuário **Editor/Admin**.
2. Menu **Dashboards → New → Import**.
3. Clique em **Upload dashboard JSON file** e selecione o arquivo, **ou** cole o conteúdo do `.json`.
4. Em **Loki datasource**, confirme que aponta para a datasource **`loki`**
   (uid `ba808642-2177-4894-931e-93c97d6ae8b3`; se o uid for outro nesse Grafana, o import
   deixa você escolher a datasource correta na tela).
5. **Import**. Pronto — o dashboard fica salvo e passa a acumular dados ao vivo.

## O que ele mostra

- **3 stats:** total de requests no período, pico de requests/hora, e nº de usuários (e-mails) distintos.
- **Ritmo de uso (barras por hora, BRT):** o horário comercial real — pico ao meio-dia, silêncio à noite/domingo, e as quedas em feriados de SP.
- **Por cliente:** linhas comparando Copercana, Rede Petro, Biopetro, Small e Setta (relógios diferentes).
- **Top usuários** e **Rotas mais acessadas** no período (tabelas com barra de gradiente).

## Detalhes técnicos

- Fuso do dashboard: **America/Sao_Paulo** (BRT), então o eixo do tempo já sai em horário local.
- Variável **`tenant`** (textbox, default `base_compartilhada`) — troque no topo para analisar
  outro tenant sem editar as queries.
- Todas as queries filtram `environment="prod"` e `user_email!=""` (só clientes reais, sem bots
  varrendo `/api/env/` etc.), e isolam o tenant com
  `|= "$tenant" | pattern "<lvl> <js>" | line_format "{{.js}}" | json | tenant_schema="$tenant"`
  (o prefixo `INFO ` do `api.log` quebra o `| json` direto).
- **Supera a retenção de 7 dias do Loki:** como o painel consulta ao vivo e fica salvo, cada
  visita mostra a janela atual — e ao acumular semanas o padrão semanal fica confiável
  (a limitação do estudo estático era justamente ver só 1 semana por vez).

## Para automatizar a criação (opcional, para o dev)

Se quiser versionar/provisionar isso sem depender de import manual, dá para:
- usar **provisioning** do Grafana (`provisioning/dashboards/*.yaml` + este JSON), ou
- gerar um **service account token com permissão de escrita** e dar `POST /api/dashboards/db`
  com `{"dashboard": <json>, "overwrite": true}`.
