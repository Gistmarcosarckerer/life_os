# LIFE OS - Contexto para Google AI Studio

Use este arquivo como contexto inicial para qualquer IA que va ajudar no desenvolvimento do LIFE OS.

## Papel esperado da IA

Voce e um arquiteto/engenheiro senior trabalhando no LIFE OS. Priorize codigo funcional, arquitetura modular, manutencao futura e decisao operacional. Nao trate o projeto como dashboard comum. O sistema deve decidir no lugar do usuario sempre que possivel.

## Produto

LIFE OS e um sistema operacional pessoal. Ele coleta dados do usuario, interpreta contexto e decide a proxima acao.

Fluxo central:

```text
INPUTS -> PROCESSAMENTO -> DECISAO -> ACAO
```

Objetivos:

- Reduzir carga mental.
- Automatizar micro-decisoes.
- Organizar prioridades dinamicamente.
- Detectar foco, dispersao e troca de contexto.
- Adaptar tarefas por energia, contexto e historico.
- Controlar financeiro pessoal e orientar decisoes de gasto.
- Permitir entrada rapida via Telegram/Siri sem abrir dashboard.

## Estado atual

Stack:

- Python
- Flask
- SQLAlchemy
- SQLite local
- PostgreSQL preparado via `DATABASE_URL`
- HTML/Jinja
- Tailwind CDN
- python-telegram-bot
- Gunicorn
- Render/Railway
- PyInstaller para executavel Windows

Estrutura:

```text
backend/
  app.py
  database.py
  models.py
  engine/
  routes/
  services/
frontend/templates/
versions/
```

## Funcionalidades existentes

### Produtividade

- Detecta janela ativa no Windows.
- Salva logs em `activity_logs`.
- Detecta troca de contexto.
- Calcula `focus_score`.
- Estado atual: `flow`, `normal`, `disperso`.
- Escolhe missao atual com base em tarefas.

### Tarefas

Modelo `Task`:

- `name`
- `impact`
- `urgency`
- `energy_required`
- `status`

Rotas:

```text
GET /tasks
POST /tasks
GET /tasks/<id>
PUT/PATCH /tasks/<id>
POST /tasks/<id>/complete
DELETE /tasks/<id>
```

### Financeiro

Modelos:

- `FinancialProfile`
- `SpendingCategory`
- `Transaction`
- `FinancialGoal`
- `PurchaseIntention`
- `MonthlyFinancialSummary`

Funcionalidades:

- Renda mensal.
- Renda extra.
- Dia de pagamento.
- Metas financeiras.
- Transacoes.
- Categorizacao automatica.
- Alertas.
- Limite diario.
- Analise de compra.

Rotas:

```text
GET /finance
GET/POST /finance/settings
GET/POST /finance/transactions
POST /finance/purchase-check
GET/POST /finance/goals
GET /api/finance/summary
```

### Telegram/Siri

Telegram bot roda junto com Flask em thread separada.

Siri/iPhone deve enviar mensagens ao bot via Atalho iOS:

```text
Siri -> Atalho iOS -> Telegram Bot -> Flask -> Banco -> Dashboard
```

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

### NLP

Arquivo:

```text
backend/services/nlp_service.py
```

Responsabilidade:

- Normalizar mensagens.
- Extrair numeros, datas, horarios, valores monetarios, categorias e sentimento.
- Classificar em:
  - `financeiro`
  - `saude`
  - `humor`
  - `produtividade`
  - `agenda`
  - `treino`
  - `nota_geral`
- Salvar toda entrada em `raw_entries`.
- Aplicar registros estruturados quando possivel.
- Gerar resposta para Telegram.

Regra obrigatoria:

```text
Toda mensagem deve ser salva. Se nao entender, salvar como raw_input.
```

## Modelos SQLAlchemy

Arquivo:

```text
backend/models.py
```

Modelos existentes:

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

## Rotas principais

```text
GET /
GET /healthz
GET /life-status
GET /tracker-status
GET /state
POST /track
GET /telegram/status
GET /telegram/entries
GET /telegram/debug
GET /telegram/raw-entries
GET /finance
GET /api/finance/summary
```

## Arquitetura desejada

Manter separacao:

- `routes/`: HTTP e serializacao.
- `services/`: regra de negocio.
- `models.py`: persistencia.
- `engine/`: integracoes com SO.
- `templates/`: interface.

Evitar:

- Regras de negocio dentro de templates.
- Parser espalhado em varios arquivos.
- Token hardcoded.
- Dependencia de Windows em producao cloud.
- Mudancas que quebrem Render/Gunicorn.

## Deploy

Render usa:

```text
gunicorn backend.app:app
```

Arquivos:

- `Procfile`
- `render.yaml`
- `requirements.txt`
- `config.py`

Variaveis:

```text
TELEGRAM_BOT_TOKEN=
SECRET_KEY=
DATABASE_URL=
ENVIRONMENT=production
LIFE_OS_DISABLE_TRACKER=true
LIFE_OS_ENABLE_WINDOWS_TRACKER=false
```

## Render ja configurado

O servico `life_os` no Render ja tem variaveis cadastradas. Nao pedir ao usuario para colar valores reais em arquivos ou no codigo.

Chaves presentes:

```text
ENVIRONMENT
LIFE_OS_ADMIN_PASSWORD
LIFE_OS_DISABLE_TRACKER
LIFE_OS_ENABLE_WINDOWS_TRACKER
PLUGGY_CLIENT_ID
PLUGGY_CLIENT_SECRET
PLUGGY_WEBHOOK_SECRET
SECRET_KEY
TELEGRAM_BOT_TOKEN
```

`LIFE_OS_ADMIN_PASSWORD` e a senha do login privado. `PLUGGY_WEBHOOK_SECRET` protege webhook e nao e senha de login.

## UX

Estilo desejado:

- SaaS moderno.
- Dark mode.
- Sidebar.
- Cards de metricas.
- Badges de status.
- Layout responsivo.
- Pouco texto explicativo.
- Foco em decisao.

Dashboard principal deve mostrar:

- Saude financeira.
- Gasto do mes.
- Saldo previsto.
- Foco atual.
- Missao automatica.
- Recomendacao financeira.
- Alertas inteligentes.
- Atividade atual.
- Telegram/debug/NLP.

## Decisoes arquiteturais ja tomadas

- Flask mantido pela simplicidade e velocidade.
- SQLAlchemy permite SQLite agora e PostgreSQL depois.
- Telegram usa polling em thread.
- NLP separado em `nlp_service.py`.
- `raw_entries` impede perda de mensagem.
- Financeiro usa `transactions` como fonte principal.
- Tracker Windows fica em `engine/`.
- Cloud usa Gunicorn.

## Debitos tecnicos

- Adicionar Alembic.
- Migrar producao para PostgreSQL.
- Adicionar autenticacao.
- Remover parser legado de `telegram_bot.py` quando NLP estiver estavel.
- Evitar multiplos workers com Telegram polling.
- Criar testes automatizados.
- Melhorar logs de producao.
- Criar tela para revisar `raw_entries`.

## Prioridades futuras

1. PostgreSQL em producao.
2. Autenticacao.
3. Revisao e promocao de `raw_entries`.
4. IA externa para NLP.
5. Calendario real.
6. Modulo treino completo.
7. Modulo saude/habitos.
8. Observabilidade.

## Instrucao para futuras alteracoes

Ao modificar o LIFE OS:

1. Ler `PROJECT_CONTEXT.md`.
2. Ler `ARCHITECTURE.md`.
3. Preservar a arquitetura em camadas.
4. Atualizar `CHANGELOG.md` e `VERSIONS.md`.
5. Se a mudanca for relevante, criar snapshot em `versions/vX.Y.Z`.
6. Validar com `compileall backend`.
7. Publicar com:

```powershell
.\deploy_lifeos.bat "mensagem da alteracao"
```

## Frase guia

```text
Como esse sistema pode decidir no lugar do usuario?
```
