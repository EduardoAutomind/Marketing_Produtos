# Análise — Etapa 3 do Cronograma de Observabilidade (AutoChecker)

> **Item #3 — "Limpar PeriodicTask órfã do Beat (KeyError `process_scheduled_notifications`)"**
> Onda 0 (Saneamento da Base) · Camada Backend/Worker · Esforço P · Sem 1 · Status no cronograma: **Não iniciado**

**Data da análise:** 2026-06-11
**Fontes analisadas:**
- `Produtos/Autochecker/AutoChecker/worker/apps/notifications/tasks/notification_tasks.py`
- `Produtos/Autochecker/AutoChecker/shared/tasks/notification_tasks.py`
- `Produtos/Autochecker/AutoChecker/backend/apps/notifications/tasks/notification_tasks.py`
- `Produtos/Autochecker/AutoChecker/shared/tests/test_notification_tasks.py`
- `Produtos/Autochecker/AutoChecker/worker/config/celery.py` + `backend/config/celery.py`
- `Produtos/Autochecker/AutoChecker/worker/docker-compose.{dev,prod}.yml`
- `Cronograma observabilidade/AutoChecker/Cronograma_Observabilidade_AutoChecker_2026-06-03.xlsx` (aba *Cronograma*, item #3)

---

## 1. O que a Etapa 3 exige

> A task `process_scheduled_notifications` está **comentada no código** e fora de qualquer `beat_schedule`, mas o agendador **persiste o schedule fora do código**. Resta uma entrada **órfã** apontando para a task removida → **`KeyError` no dispatch** do Beat.
> Era o **maior ruído do produto**: ~1.640 eventos (clusters BACKEND-1H / WORKER-1F).

Entrega: **remover/migrar a entrada órfã persistida** e **alinhar o schedule persistido com o do código.**

---

## 2. O que cada arquivo mostrou

### 2.1 `worker/apps/notifications/tasks/notification_tasks.py`
- `process_scheduled_notifications` está **comentada** (linhas 49‑67). `cleanup_old_notification_logs` também (70‑87). → **confirma a premissa do cronograma.**
- Reexporta `process_notification_task` do `shared` (linha 13), mas **redefine localmente** `retry_failed_notifications` (linha 90).
- ⚠️ **Bug colateral:** essa versão local chama `process_notification_task.delay(notification.id)` com **1 argumento só** (linha 110), enquanto a assinatura real exige `(notification_log_id, tenant_schema_name, tenant_id)`. Em runtime → `TypeError`. É um conflito de versão com a do `shared`.

### 2.2 `shared/tasks/notification_tasks.py` (implementação canônica)
- `process_notification_task` multi-tenant (`schema_context`), com classificação de **erro permanente vs. temporário** e backoff exponencial.
- `retry_failed_notifications` **reescrita** para varrer todos os tenants ativos (`_retry_failed_notifications_for_tenant`), pois `NotificationLog` vive em `TENANT_APPS`. Versão correta e robusta.
- **Nenhuma referência** a `process_scheduled_notifications` nem à entrada órfã.

### 2.3 `backend/apps/notifications/tasks/notification_tasks.py`
- Apenas um shim `DEPRECATED` que reimporta do `shared`. Correto, sem relação com a Etapa 3.

### 2.4 `shared/tests/test_notification_tasks.py`
- Cobre **só** `retry_failed_notifications` / `_retry_failed_notifications_for_tenant`. **Não testa** `process_scheduled_notifications` nem a limpeza do schedule órfão.

### 2.5 Configuração do Beat
- `worker/config/celery.py:69` define `beat_schedule` no código — e **não contém** `process_scheduled_notifications`. ✅
- `backend/config/celery.py:23‑25` deliberadamente **não define** `beat_schedule`. ✅

---

## 3. ⚠️ Discrepância encontrada — corrigir no cronograma antes de executar

O cronograma assume que a órfã está no **DB do `django-celery-beat` (`PeriodicTask`)**. Mas o Beat real roda com **PersistentScheduler (arquivo shelve)**, não com o `DatabaseScheduler`:

```
celery -A config beat --schedule=/tmp/celerybeat-schedule   (docker-compose.prod.yml:135 / dev.yml:120)
```

- **Não há** flag `--scheduler django_celery_beat.schedulers:DatabaseScheduler` nem setting `CELERY_BEAT_SCHEDULER`.
- `django_celery_beat` está no `INSTALLED_APPS` (`worker/config/settings/base.py:49`) mas **não está em uso** como scheduler.
- O volume `/tmp:/tmp` (compose) torna o arquivo **persistente entre restarts** → a órfã sobrevive a `docker compose restart`.

**Conclusão:** a órfã muito provavelmente está no **arquivo `/tmp/celerybeat-schedule`** (shelve), e **não** no DB. Pode também haver `PeriodicTask` no banco se em algum momento alguém rodou com `DatabaseScheduler`. **Verificar os dois.**

---

## 4. Veredito: ❌ NÃO cumprida (no máximo parcial — lado do código)

| O que | Situação |
|---|---|
| Task comentada em todo lugar (`tasks.py`, `tasks/__init__.py`, `…/notification_tasks.py`) | ✅ já estava |
| `beat_schedule` do código sem a task | ✅ ok |
| `backend/config/celery.py` sem `beat_schedule` | ✅ ok |
| **Expurgo da entrada órfã persistida** (`/tmp/celerybeat-schedule` e/ou `PeriodicTask`) | ❌ **não feito** |
| Alinhar schedule persistido × código | ❌ não feito |
| Teste cobrindo a regressão | ❌ inexistente |
| **Status geral** | **❌ Não cumprida — "Não iniciado" confere** |

> Comentar a task foi justamente o que *criou* a órfã. O lado do código já está limpo; falta o expurgo **runtime/ops**, que **nenhum** dos 4 arquivos faz (e nem poderia — não é mudança de código-fonte).

---

## 5. Como fazer — plano concreto

### Passo 0 — Diagnosticar onde a órfã vive
- **Container beat:** inspecionar `/tmp/celerybeat-schedule*` (shelve). Procurar a chave `process_scheduled_notifications`.
- **DB:** `PeriodicTask.objects.filter(task__icontains='process_scheduled_notifications')`.

### Passo 1 — Expurgar (a real entrega da Etapa 3)
- **Se for o arquivo shelve (mais provável):** parar o beat, **apagar `/tmp/celerybeat-schedule*`** e subir de novo — ele recria a partir do `beat_schedule` do código (a fonte de verdade hoje).
  ```bash
  docker compose -p prod stop beat
  docker compose -p prod run --rm beat bash -lc 'rm -f /tmp/celerybeat-schedule*'
  docker compose -p prod up -d beat
  ```
- **Se houver linha no DB:** criar uma **data migration idempotente** (versionada, roda em todo ambiente) em vez de deletar à mão:
  ```python
  def remove_orphan(apps, schema_editor):
      PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')
      PeriodicTask.objects.filter(task__endswith='process_scheduled_notifications').delete()
  ```

### Passo 2 — Travar a fonte de verdade (evitar reincidência)
- Escolher **um** modelo de schedule. Como o `beat_schedule` no código já é a fonte real, **manter o file scheduler** e **não** misturar com `DatabaseScheduler`. Misturar os dois é o que gera órfãs. (Se um dia quiser gestão via Admin, migrar de vez para `DatabaseScheduler` + `setup_periodic_tasks`.)

### Passo 3 — Corrigir o bug colateral (item 2.1)
- Remover a `retry_failed_notifications` **local e bugada** do `worker/apps/notifications/tasks/notification_tasks.py` e **reexportar a do `shared`** (igual ao backend faz). Senão a fila `notifications_retry` pode pegar a versão quebrada (1 arg → `TypeError`).

### Passo 4 — Validar / fechar a etapa
- Subir o beat e confirmar nos logs que **não há mais `KeyError: process_scheduled_notifications`** no dispatch.
- Confirmar no Sentry a queda dos clusters **BACKEND-1H / WORKER-1F** (KPI implícito: ~1.640 ev → ~0).
- Adicionar um **teste de guarda**: importar cada `task` do `beat_schedule` e afirmar que está registrada no app Celery (`app.tasks`), pegando qualquer símbolo inexistente em CI.

---

## 6. Ressalvas antes de mexer

- O expurgo do `/tmp/celerybeat-schedule` é **runtime** — precisa ser rodado no ambiente (não versiona em código).
- Apagar pasta/arquivo de ambiente ou rodar migration de delete → **confirmar antes**.
- Confirmar se algum host já rodou com `DatabaseScheduler` (decide se a migration do Passo 1 é necessária).

---

## 7. Resumo executivo

| Entrega da Etapa 3 | Situação |
|---|---|
| Task `process_scheduled_notifications` fora do código | ✅ já estava (foi o que criou a órfã) |
| Expurgo da entrada órfã persistida | ❌ não feito |
| Local correto da órfã identificado | ⚠️ cronograma diz "DB"; evidência aponta **arquivo `/tmp/celerybeat-schedule`** |
| Alinhar schedule persistido × código | ❌ não feito |
| Bug colateral `retry_failed_notifications` (worker, 1 arg) | ❌ a corrigir junto |
| Teste de regressão | ❌ inexistente |
| **Status geral** | **❌ Não cumprida — "Não iniciado" confere com o código** |
