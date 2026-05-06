# LIFE OS Versions

Este arquivo registra as versoes criadas pelo Codex para facilitar retorno manual.

## v0.1.0 - Nucleo de foco e atividade

- Rastreamento de janela ativa no Windows.
- Logs de atividade no SQLite.
- Calculo de foco.
- Deteccao de estado: flow, normal, disperso.
- Endpoint `/life-status`.
- Missao automatica inicial baseada em tarefas.

## v0.2.0 - Tarefas e rastreamento continuo

- CRUD completo de tarefas via API.
- Interface para criar, listar, concluir e remover tarefas.
- Rastreador de atividade iniciado automaticamente junto com o Flask.
- Endpoint `/tracker-status`.
- Snapshot local em `versions/v0.2.0`.

## v0.2.1 - Correcao do executavel

- Corrigido loop infinito de paginas ao abrir `LifeOS.exe`.
- Removido uso de `subprocess` com `sys.executable` no inicializador empacotado.
- Flask agora roda no mesmo processo do executavel.
- Navegador abre uma unica vez; se o servidor ja estiver ativo, apenas reutiliza a aba.
- Templates incluidos no arquivo `.spec` do PyInstaller.

## v0.3.0 - Sistema vivo em tempo real

- Captura real do Windows consolidada por sessao de janela/app.
- Troca de contexto detectada por mudanca de app ou titulo da janela.
- Focus score recalculado automaticamente pela janela recente de atividade.
- Estado `flow`, `normal` ou `disperso` atualizado em tempo real.
- Missao principal recalculada automaticamente e marcada como `active`.
- `/life-status` retorna atividade atual, apps dominantes e timestamp de atualizacao.
- Interface atualiza score, estado, missao, atividade atual, apps e fila de tarefas sem clique.

## v0.4.0 - Integracao Telegram

- Adicionado `backend/services/telegram_bot.py`.
- Bot usa `python-telegram-bot` e le `TELEGRAM_BOT_TOKEN` do ambiente.
- Parser aceita entradas simples de peso, sono, gastos, humor, tarefas e treino.
- Novas tabelas: `mobile_entries`, `expenses`, `body_metrics`, `mood_logs`, `task_entries`.
- Bot salva registros no SQLite e responde com interpretacao e recomendacao.
- Telegram inicia junto com Flask em thread separada sem travar o servidor.
- Endpoints `/telegram/status` e `/telegram/entries`.
- Dashboard mostra status do bot e ultimos registros recebidos.

## v0.4.1 - Build do executavel na raiz

- Adicionado `build_lifeos.ps1`.
- Adicionado `build_lifeos.bat`.
- Build passa a copiar o executavel para `LifeOS.exe` na pasta principal.
- Build tambem cria copia historica em `executables/LifeOS-<versao>.exe`.

## v0.5.0 - Deploy Render/Railway

- Adicionado `config.py` com variaveis de ambiente e suporte a SQLite/PostgreSQL.
- Adicionado `Procfile` com `web: gunicorn backend.app:app`.
- Adicionado `.env.example` sem segredos reais.
- Adicionado `render.yaml`.
- `requirements.txt` inclui `python-dotenv`, `python-telegram-bot`, `gunicorn` e `psycopg2-binary`.
- `app.run` local usa `debug=False` e porta por `PORT`.
- Gunicorn passa a usar `backend.app:app` em producao.
- Tracker Windows fica desativado em nuvem Linux por configuracao.
- Adicionado endpoint `/healthz`.
- README atualizado com instrucoes de deploy em Render e Railway.

## v0.6.0 - Financeiro profissional e dashboard premium

- Adicionados modelos financeiros: `financial_profile`, `transactions`, `spending_categories`, `purchase_intentions`, `financial_goals`, `monthly_financial_summary`.
- Adicionado `backend/services/finance_service.py` com resumo mensal, alertas, categorizacao e analise de compra.
- Adicionado `backend/routes/finance.py`.
- Novas rotas: `/finance`, `/finance/settings`, `/finance/transactions`, `/finance/purchase-check`, `/finance/goals`, `/api/finance/summary`.
- Telegram entende `gasto`, `gastei`, `paguei`, `recebi` e `renda extra`.
- Dashboard principal mostra saude financeira, risco, gasto do mes, saldo previsto e recomendacao.
- UI reformulada com sidebar, header, cards premium e paginas para Dashboard, Financeiro, Produtividade, Telegram e Configuracoes.
