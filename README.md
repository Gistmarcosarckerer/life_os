# LIFE OS

LIFE OS e um sistema operacional pessoal para decisao diaria. O objetivo nao e ser um dashboard nem um gerenciador de tarefas comum. O sistema captura sinais do usuario, interpreta contexto, calcula foco, organiza prioridades e decide qual deve ser a proxima missao operacional.

## Visao geral

O LIFE OS trabalha no fluxo:

```text
INPUTS -> PROCESSAMENTO -> DECISAO -> ACAO
```

Inputs podem vir do Windows, dashboard, Telegram ou Siri/iPhone. O backend interpreta esses dados, salva historico, calcula estado atual e retorna uma recomendacao objetiva.

## Proposito

- Reduzir carga mental.
- Automatizar micro-decisoes.
- Priorizar tarefas por impacto, urgencia e energia.
- Detectar foco, dispersao e troca de contexto.
- Registrar dados pessoais sem abrir o dashboard.
- Apoiar decisoes financeiras e operacionais.

## Funcionalidades principais

- Rastreamento de janela ativa no Windows.
- Logs de atividade por aplicativo.
- Calculo automatico de `focus_score`.
- Deteccao de estado: `flow`, `normal`, `disperso`.
- Motor de decisao para escolher a missao atual.
- CRUD de tarefas.
- Tracker em background junto com o Flask.
- Integracao Telegram via `python-telegram-bot`.
- Entrada por Siri/iPhone usando atalho que envia mensagem ao bot do Telegram.
- Parser NLP simples para linguagem natural.
- Modulo financeiro com transacoes, renda, metas, resumo mensal e analise de compra.
- Dashboard premium em HTML + Tailwind CDN.
- Deploy preparado para Render/Railway com Gunicorn.

## Stack

- Python
- Flask
- SQLAlchemy
- SQLite local
- PostgreSQL preparado para producao futura
- HTML + Tailwind CSS via CDN
- python-dotenv
- python-telegram-bot
- Gunicorn
- PyInstaller para executavel Windows local

## Como rodar localmente

```powershell
cd C:\Users\makin\Desktop\life_os\life_os
pip install -r requirements.txt
python backend/app.py
```

Acesse:

```text
http://127.0.0.1:5000
```

## Como rodar em producao

Nao use o servidor Flask puro em producao. Use Gunicorn:

```bash
gunicorn backend.app:app
```

O `Procfile` ja esta configurado:

```text
web: gunicorn backend.app:app
```

## Deploy Render

Configuracao recomendada:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn backend.app:app
```

Variaveis no Render:

```text
ENVIRONMENT=production
SECRET_KEY=<valor_seguro>
TELEGRAM_BOT_TOKEN=<token_do_bot>
DATABASE_URL=
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

Observacao: SQLite em Render pode ser efemero se nao houver disco persistente. Para uso real continuo, migrar para PostgreSQL.

## Variaveis de ambiente

Exemplo em `.env.example`:

```text
TELEGRAM_BOT_TOKEN=
SECRET_KEY=
DATABASE_URL=
ENVIRONMENT=production
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

## Integracao Telegram

O bot inicia junto com Flask em thread separada e nao bloqueia o servidor. O token deve vir apenas de `TELEGRAM_BOT_TOKEN`.

Exemplos aceitos:

```text
gastei 80 mercado
gasto 120 mercado
paguei 900 carro
recebi 4300 salario
peso 88
sono 6h
to cansado hoje
dormi mal
humor 7 energia 6 ansiedade 3
tarefa revisar PCP impacto 8 urgencia 7 energia 5
amanha consulta 14h
treino peito concluido
```

Toda mensagem e salva. Quando o NLP nao entende totalmente, o texto entra em `raw_entries` com status `raw_input`.

## Integracao Siri/iPhone

O caminho atual recomendado e:

```text
Siri -> Atalho iOS -> Telegram Bot -> Flask backend -> SQLite/PostgreSQL -> Dashboard
```

O usuario cria um atalho no iPhone para enviar uma mensagem ao bot. O LIFE OS recebe como se fosse uma mensagem normal do Telegram.

## Screenshots

Placeholders para documentacao visual:

```text
docs/screenshots/dashboard.png
docs/screenshots/finance.png
docs/screenshots/telegram-debug.png
docs/screenshots/mobile-siri-flow.png
```

## Estrutura de pastas

```text
backend/
  app.py
  database.py
  models.py
  engine/
  routes/
  services/
frontend/
  templates/
versions/
executables/
build/
dist/
```

## Comandos uteis

Rodar local:

```powershell
python backend/app.py
```

Gerar executavel Windows:

```powershell
.\build_lifeos.ps1
```

Publicar alteracoes para GitHub/Render:

```powershell
.\deploy_lifeos.bat "mensagem da alteracao"
```

Validar sintaxe Python:

```powershell
.\.venv\Scripts\python.exe -m compileall backend
```

## Endpoints principais

```text
GET /
GET /healthz
GET /life-status
GET /tracker-status
GET /state
POST /track
GET /tasks
POST /tasks
GET /tasks/<id>
PATCH /tasks/<id>
POST /tasks/<id>/complete
DELETE /tasks/<id>
GET /finance
GET /finance/settings
POST /finance/settings
GET /finance/transactions
POST /finance/transactions
POST /finance/purchase-check
GET /finance/goals
POST /finance/goals
GET /api/finance/summary
GET /telegram/status
GET /telegram/entries
GET /telegram/debug
GET /telegram/raw-entries
```

## Roadmap resumido

- Migrar dados de producao para PostgreSQL.
- Adicionar autenticacao.
- Criar painel de revisao das `raw_entries`.
- Adicionar calendario real para agenda.
- Conectar IA externa para interpretacao semantica avancada.
- Criar modulo de habitos, saude e treino com modelos proprios.
- Melhorar observabilidade e logs de producao.

## Documentacao complementar

- `PROJECT_CONTEXT.md`: memoria permanente para Codex/IA.
- `ARCHITECTURE.md`: arquitetura tecnica e fluxos.
- `CHANGELOG.md`: historico no formato Keep a Changelog.
- `VERSIONS.md`: snapshots e estabilidade por versao.
- `AI_STUDIO_CONTEXT.md`: contexto consolidado para colar no Google AI Studio.
