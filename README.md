# LIFE OS

Sistema operacional pessoal em Flask para rastrear atividade, calcular foco, decidir a missao atual e receber entradas pelo Telegram.

## Versoes

O Codex cria snapshots em `versions/` a cada atualizacao relevante.

- `versions/v0.1.0`: nucleo inicial de foco, atividade e missao.
- `versions/v0.2.0`: CRUD de tarefas e rastreador automatico em background.
- `versions/v0.2.1`: correcao do executavel que abria paginas infinitas.
- `versions/v0.3.0`: captura real consolidada, focus score e missao em tempo real.
- `versions/v0.4.0`: integracao com Telegram para entradas moveis.
- `versions/v0.5.0`: preparacao para deploy em Render/Railway com Gunicorn.
- `versions/v0.6.0`: modulo financeiro profissional e dashboard premium.

Para voltar manualmente, copie os arquivos da versao desejada de volta para a raiz do projeto.

## Rodar localmente

```powershell
pip install -r requirements.txt
python backend/app.py
```

Acesse:

```text
http://127.0.0.1:5000
```

O painel consulta `/life-status` a cada poucos segundos e atualiza estado, focus score e missao sem intervencao manual.

## Variaveis de ambiente

Copie `.env.example` para `.env` em desenvolvimento local.

```text
TELEGRAM_BOT_TOKEN=
SECRET_KEY=
DATABASE_URL=
ENVIRONMENT=production
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

`DATABASE_URL` e opcional. Sem ela, o sistema usa SQLite em `life_os.db`.

Para PostgreSQL no futuro, defina:

```text
DATABASE_URL=postgresql://usuario:senha@host:5432/banco
```

## Telegram

Configure o token do bot antes de iniciar:

```powershell
$env:TELEGRAM_BOT_TOKEN="seu_token_aqui"
python backend/app.py
```

Mensagens aceitas:

```text
peso 88.1
sono 6h
gastei 45 almoco
gasto 120 mercado
paguei 950 parcela carro
recebi 4300 salario
renda extra 300 freela
humor 7 energia 6 ansiedade 3
tarefa revisar PCP impacto 8 urgencia 7 energia 5
treino peito concluido
```

O bot salva os dados no SQLite/PostgreSQL, responde com a interpretacao e sugere uma proxima recomendacao quando possivel.

## Financeiro

O LIFE OS possui um modulo financeiro em `/finance` com:

- configuracao de renda mensal liquida
- renda extra opcional
- dia de recebimento
- meta de economia mensal
- reserva de emergencia
- registro de gastos e renda
- categorizacao automatica
- alertas inteligentes
- limite diario recomendado
- analise de intencao de compra

Comandos financeiros pelo Telegram:

```text
gastei 35 almoco
gasto 120 mercado
paguei 950 parcela carro
recebi 4300 salario
renda extra 300 freela
```

## Producao

Nao use `python backend/app.py` em producao. Use Gunicorn:

```bash
gunicorn backend.app:app
```

O `Procfile` ja esta configurado:

```text
web: gunicorn backend.app:app
```

O tracker de janela ativa do Windows fica desativado por padrao em nuvem Linux. Para PC local Windows, ele pode continuar ativo.

## Deploy no Render

1. Envie o projeto para um repositorio GitHub.
2. Crie um novo Web Service no Render apontando para o repositorio.
3. Configure:

```text
Build command: pip install -r requirements.txt
Start command: gunicorn backend.app:app
```

4. Configure as variaveis de ambiente:

```text
ENVIRONMENT=production
SECRET_KEY=<valor_aleatorio_seguro>
TELEGRAM_BOT_TOKEN=<token_do_bot>
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

5. Opcional: configure `DATABASE_URL` para PostgreSQL. Sem isso, o app usa SQLite local do servidor.
6. Abra a URL publica gerada pelo Render.

Tambem existe `render.yaml` para Blueprint Deploy.

## Deploy no Railway

1. Envie o projeto para GitHub.
2. No Railway, escolha Deploy from GitHub Repo.
3. Configure as variaveis:

```text
ENVIRONMENT=production
SECRET_KEY=<valor_aleatorio_seguro>
TELEGRAM_BOT_TOKEN=<token_do_bot>
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

4. Railway detecta o `Procfile` e inicia:

```text
gunicorn backend.app:app
```

5. Gere um dominio publico no painel do Railway.
6. Opcional: adicione PostgreSQL e use a variavel `DATABASE_URL`.

## Endpoints principais

```text
GET /
GET /healthz
GET /life-status
GET /tracker-status
GET /telegram/status
GET /telegram/entries
GET /finance
GET /finance/settings
POST /finance/settings
GET /finance/transactions
POST /finance/transactions
POST /finance/purchase-check
GET /api/finance/summary
POST /track
```

`/life-status` retorna:

- `focus_score`
- `estado_atual`
- `missao_atual`
- `recomendacao`
- `atividade_atual`
- `top_apps`
- `atualizado_em`
- metricas de troca de contexto e tempo por categoria

## CRUD de tarefas

```text
GET /tasks
GET /tasks?include_done=false
POST /tasks
GET /tasks/<id>
PATCH /tasks/<id>
PUT /tasks/<id>
POST /tasks/<id>/complete
DELETE /tasks/<id>
```

## Executavel Windows

O executavel principal deve ficar sempre na pasta raiz:

```text
C:\Users\makin\Desktop\life_os\life_os\LifeOS.exe
```

Para gerar ou atualizar:

```powershell
.\build_lifeos.ps1
```

Esse script tambem guarda uma copia versionada em `executables/`.

## Arquitetura

- `backend/engine`: integracao com recursos do sistema operacional.
- `backend/services`: regras de produtividade, rastreamento, tarefas, Telegram e decisao.
- `backend/services/finance_service.py`: calculos financeiros, alertas, categorias e compra.
- `backend/routes`: endpoints HTTP.
- `backend/models.py`: modelos SQLAlchemy.
- `frontend/templates`: interface simples focada na decisao.
