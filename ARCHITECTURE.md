# ARCHITECTURE - LIFE OS

## Resumo tecnico

LIFE OS e uma aplicacao Flask com arquitetura modular em camadas. O backend concentra regras de decisao, NLP, produtividade, financeiro e integracoes. O frontend e HTML/Jinja com Tailwind CDN. O banco usa SQLAlchemy com SQLite local e preparo para PostgreSQL.

## Estrutura de pastas

```text
life_os/
  backend/
    app.py
    database.py
    models.py
    engine/
      windows_activity.py
    routes/
      dashboard.py
      finance.py
      productivity.py
      tasks.py
      telegram.py
    services/
      activity_tracker.py
      background_tracker.py
      decision_engine.py
      finance_service.py
      mobile_entry_service.py
      nlp_service.py
      productivity_engine.py
      task_service.py
      telegram_bot.py
  frontend/
    templates/
      base.html
      dashboard.html
      finance.html
      gym.html
      productivity.html
      settings.html
      telegram.html
  versions/
  executables/
  config.py
  Procfile
  render.yaml
  requirements.txt
```

## Responsabilidades

### `backend/app.py`

- Cria o Flask app.
- Inicializa banco.
- Registra blueprints.
- Semeia tarefas e categorias financeiras.
- Inicia tracker em background quando configurado.
- Inicia Telegram bot.
- Expõe `/healthz`.

### `backend/database.py`

- Configura engine SQLAlchemy.
- Usa `DATABASE_URL`.
- Mantem SQLite local como padrao.
- Aplica migracoes leves para colunas antigas.
- Fornece `session_scope()`.

### `backend/models.py`

Define modelos persistidos:

- `Task`
- `ActivityLog`
- `MobileEntry`
- `Expense`
- `BodyMetric`
- `MoodLog`
- `TaskEntry`
- `RawEntry`
- `FinancialProfile`
- `SpendingCategory`
- `Transaction`
- `FinancialGoal`
- `PurchaseIntention`
- `MonthlyFinancialSummary`

### `backend/engine`

Camada de integracao com sistema operacional. Atualmente contem `WindowsActivityReader`, que usa APIs do Windows para detectar janela ativa, titulo e processo.

### `backend/services`

Camada de regra de negocio:

- `activity_tracker.py`: captura atividade e grava logs.
- `background_tracker.py`: loop em thread para captura continua.
- `productivity_engine.py`: calcula foco, estado e resumo.
- `decision_engine.py`: escolhe missao atual.
- `task_service.py`: CRUD e validacao de tarefas.
- `finance_service.py`: financeiro, alertas, categorias, compra.
- `telegram_bot.py`: ciclo de vida do bot e recebimento de mensagens.
- `mobile_entry_service.py`: registros moveis e debug Telegram.
- `nlp_service.py`: classificacao e extracao de linguagem natural.
- `inbox_service.py`: revisao de entradas, correcoes, tarefas/transacoes e regras pessoais.

### `backend/routes`

Camada HTTP. Deve permanecer fina.

## Fluxo geral

```text
Usuario
  |
  |-- Dashboard HTML
  |-- Telegram
  |-- Siri/iPhone
  |-- Windows activity
        |
        v
Flask routes / services
        |
        v
SQLAlchemy models
        |
        v
SQLite local / PostgreSQL futuro
        |
        v
Dashboard + resposta Telegram
```

## Fluxo Telegram -> backend -> banco -> dashboard

```text
Telegram message
  |
  v
telegram_bot.py
  |
  v
process_telegram_message()
  |
  v
nlp_service.analyze_message()
  |
  +--> RawEntry sempre salvo
  |
  +--> apply_analysis()
        |
        +--> Transaction / Expense
        +--> BodyMetric
        +--> MoodLog
        +--> Task / TaskEntry
  |
  v
MobileEntry salvo para historico/debug
  |
  v
Resposta ao Telegram
  |
  v
Dashboard consulta /telegram/entries, /telegram/debug e /telegram/raw-entries
```

## Fluxo Siri -> Telegram -> backend

```text
Usuario fala com Siri
  |
  v
Atalho iOS envia texto ao Telegram Bot
  |
  v
Mesmo fluxo Telegram normal
```

## Fluxo produtividade

```text
WindowsActivityReader
  |
  v
ActivityTracker.capture_once()
  |
  v
ActivityLog
  |
  v
productivity_engine.get_focus_snapshot()
  |
  v
decision_engine.choose_current_mission()
  |
  v
/life-status
  |
  v
Dashboard atualiza a cada poucos segundos
```

## Fluxo financeiro

```text
Dashboard ou Telegram
  |
  v
finance_service.create_transaction()
  |
  v
Transaction
  |
  v
finance_service.get_financial_summary()
  |
  v
Cards, alertas, limite diario, risco e recomendacao
```

## Rotas existentes

### Dashboard

```text
GET /
GET /productivity
GET /telegram
GET /gym
GET /settings
```

### Produtividade

```text
GET /state
POST /track
GET /tracker-status
GET /life-status
```

### Tarefas

```text
GET /tasks
POST /tasks
GET /tasks/<id>
PUT /tasks/<id>
PATCH /tasks/<id>
POST /tasks/<id>/complete
DELETE /tasks/<id>
```

### Financeiro

```text
GET /finance
GET /finance/settings
POST /finance/settings
GET /finance/transactions
POST /finance/transactions
POST /finance/purchase-check
GET /finance/goals
POST /finance/goals
GET /api/finance/summary
```

### Telegram

```text
GET /telegram/status
GET /telegram/entries
GET /telegram/debug
GET /telegram/raw-entries
```

### Inbox

```text
GET /inbox
GET /api/inbox/summary
GET /api/inbox/items
POST /api/inbox/items/<id>/review
GET /api/inbox/rules
POST /api/inbox/rules
```

## Banco de dados

### Local

Padrao:

```text
sqlite:///life_os.db
```

### Producao

Preparado para:

```text
postgresql://usuario:senha@host:5432/banco
```

Atualmente nao ha Alembic. `Base.metadata.create_all()` cria tabelas novas. Migracoes pontuais SQLite estao em `apply_lightweight_migrations()`.

## Deploy cloud

Render/Railway usam:

```text
gunicorn backend.app:app
```

Arquivos relevantes:

- `Procfile`
- `render.yaml`
- `requirements.txt`
- `config.py`

## Trackers

O tracker Windows deve rodar apenas em ambiente local Windows. Na nuvem Linux, deve ficar desligado:

```text
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

## NLP layer

Arquivo principal:

```text
backend/services/nlp_service.py
```

Responsabilidades:

- Normalizar texto.
- Extrair numeros, datas, horarios, valores e sentimento.
- Classificar dominio.
- Salvar `RawEntry`.
- Aplicar registros estruturados.
- Gerar resposta para Telegram.

Essa camada foi separada para permitir troca futura por IA sem reescrever Telegram, rotas ou financeiro.

## Inbox layer

Arquivo principal:

```text
backend/services/inbox_service.py
```

Fluxo:

```text
raw_entries
  |
  v
/inbox
  |
  +--> confirmar interpretacao
  +--> ignorar ruido
  +--> criar transacao
  +--> criar tarefa
  +--> criar regra pessoal
```

Campos de revisao em `RawEntry`:

- `review_status`
- `review_decision`
- `reviewed_at`

Tabela de regras:

- `personal_rules`

Objetivo: criar memoria operacional limpa antes de automatizar mais decisoes.

## Decisoes de separacao

- Rotas nao devem conter regras pesadas.
- Services concentram comportamento.
- Models nao devem conter logica complexa.
- Engine isola dependencia de Windows.
- NLP nao deve depender do dashboard.
- Financeiro nao deve depender do Telegram.
- Telegram deve apenas receber, chamar servicos e responder.

## Pontos de extensao futura

- `nlp_service.py`: substituir heuristicas por LLM mantendo contrato de saida.
- `database.py`: adicionar Alembic.
- `finance_service.py`: adicionar orcamentos recorrentes e parcelas reais.
- `task_service.py`: adicionar projetos e recorrencia.
- `productivity_engine.py`: adicionar historico por horario.
- `telegram_bot.py`: migrar polling para webhook em producao se necessario.
- `frontend/templates`: evoluir para componentes ou framework frontend se o HTML crescer demais.
