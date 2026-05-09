# Changelog

Todas as mudancas relevantes do LIFE OS devem ser documentadas neste arquivo.

Formato inspirado em Keep a Changelog.

## v0.12.0 - Seguranca para dados reais

### Added

- Login privado com `LIFE_OS_ADMIN_PASSWORD`.
- Rota `/login` e template `login.html`.
- Rota `/logout`.
- Servico `security_service.py`.
- CSRF para metodos `POST`, `PUT`, `PATCH` e `DELETE`.
- Headers de seguranca basicos.
- Bloqueio de rotas privadas em producao quando senha admin nao estiver configurada.
- Webhook Pluggy protegido por `PLUGGY_WEBHOOK_SECRET`.

### Changed

- `base.html`, `finance.html` e `inbox.html` passam a enviar token CSRF nos POSTs.
- Connect Token Pluggy passa a registrar webhook com segredo na query string.

### Fixed

- Acesso publico irrestrito ao dashboard e APIs privadas.
- Webhook Pluggy sem validacao minima.

### Removed

- Nada removido.

## v0.11.0 - Inbox inteligente

### Added

- Campos de revisao em `raw_entries`: `review_status`, `review_decision`, `reviewed_at`.
- Modelo `PersonalRule` e tabela `personal_rules`.
- Servico `backend/services/inbox_service.py`.
- Rotas `/inbox` e APIs `/api/inbox/*`.
- Tela de Inbox operacional para revisar, confirmar, ignorar, criar transacoes, criar tarefas e cadastrar regras pessoais.
- Link de Inbox na sidebar.

### Changed

- Documentacao atualizada para tratar `raw_entries` como fonte de revisao operacional.

### Fixed

- Entradas nao classificadas deixam de ficar apenas como historico e passam a ter fluxo de decisao.

### Removed

- Nada removido.

## v0.10.0 - Integracao Pluggy/Open Finance

### Added

- Configuracao `PLUGGY_CLIENT_ID`, `PLUGGY_CLIENT_SECRET`, `PLUGGY_WEBHOOK_SECRET`.
- Modelos `BankConnection`, `BankAccount` e `ImportedTransaction`.
- Servico `backend/services/pluggy_service.py`.
- Endpoints para gerar Connect Token, registrar item, sincronizar bancos e receber webhook.
- Interface em `/finance` para conectar banco via Pluggy Connect Widget.
- Importacao de transacoes Pluggy para `transactions` do LIFE OS.

### Changed

- `/api/finance/summary` agora inclui status Pluggy e contas bancarias conectadas.
- `requirements.txt` inclui `requests`.

### Fixed

- Dedupe de transacoes importadas via tabela `imported_transactions`.

### Removed

- Nada removido.

## v0.9.0 - Interface inspirada no modelo Centric

### Added

- Linguagem visual clara inspirada no modelo em `C:\Users\makin\Desktop\cetric\centric`.
- Cards de metricas com acentos indigo, laranja, branco e escuro.
- Sidebar com identidade visual, icones textuais e bloco de saude do sistema.

### Changed

- `base.html` passou de dashboard escuro para visual claro SaaS/mobile-first.
- `dashboard.html` recebeu cards grandes arredondados e hierarquia visual mais proxima do modelo.
- Componentes globais `panel`, `panel-soft`, `field`, `btn`, `badge` e navegacao foram reestilizados.

### Fixed

- Contraste geral da interface em paginas herdadas dos templates.

### Removed

- Nada removido.

## v0.8.0 - Documentacao de longo prazo

### Added

- `PROJECT_CONTEXT.md` como memoria permanente para Codex/IA.
- `ARCHITECTURE.md` com estrutura tecnica, fluxos e pontos de extensao.
- `AI_STUDIO_CONTEXT.md` consolidado para Google AI Studio.
- README reestruturado em formato profissional.
- `VERSIONS.md` reestruturado com status de estabilidade.

### Changed

- Documentacao passou a refletir o estado real do LIFE OS e nao apenas comandos basicos.
- Projeto agora possui base documental para continuidade entre contextos.

### Fixed

- Falta de contexto persistente para futuras IAs.

### Removed

- Nada removido.

## v0.7.0 - Parser NLP livre Telegram/Siri

### Added

- Modelo `RawEntry` e tabela `raw_entries`.
- Servico `backend/services/nlp_service.py`.
- Classificacao de mensagens em financeiro, saude, humor, produtividade, agenda, treino e nota geral.
- Extracao de numeros, datas, horarios, valores monetarios, categorias e sentimento simples.
- Endpoint `/telegram/raw-entries`.
- Secao no dashboard para entradas interpretadas, nao classificadas e sugestoes automaticas.

### Changed

- Telegram passou a analisar toda mensagem com NLP antes de aplicar registros estruturados.
- Mensagens financeiras continuam criando `transactions` e atualizando o resumo financeiro.
- Mensagens nao entendidas passam a ser salvas como `raw_input`.

### Fixed

- Reduzido risco de perda de mensagens recebidas por Telegram/Siri.

### Removed

- Nada removido. Parser legado ainda existe em `telegram_bot.py` para futura limpeza.

## v0.6.0 - Financeiro profissional e dashboard premium

### Added

- Modelos financeiros: `FinancialProfile`, `SpendingCategory`, `Transaction`, `FinancialGoal`, `PurchaseIntention`, `MonthlyFinancialSummary`.
- Servico `finance_service.py`.
- Rotas `/finance`, `/finance/settings`, `/finance/transactions`, `/finance/purchase-check`, `/finance/goals` e `/api/finance/summary`.
- Categorizacao automatica de gastos.
- Resumo mensal.
- Alertas financeiros inteligentes.
- Analise de intencao de compra.
- Dashboard escuro premium com sidebar, cards e secoes operacionais.

### Changed

- Dashboard principal passou a incluir saude financeira, risco, gasto mensal, saldo previsto e recomendacao financeira.
- Telegram passou a registrar gastos e receitas na tabela `transactions`.

### Fixed

- Melhor alinhamento entre registros Telegram e dashboard financeiro.

### Removed

- Nada removido.

## v0.5.0 - Deploy cloud Render/Railway

### Added

- `config.py` com variaveis de ambiente.
- `Procfile` com `web: gunicorn backend.app:app`.
- `.env.example`.
- `render.yaml`.
- Endpoint `/healthz`.
- Suporte a `DATABASE_URL`.
- Gunicorn em `requirements.txt`.

### Changed

- Flask local passou a rodar com `debug=False`.
- Tracker Windows passou a ser controlado por flags para evitar erro em Linux.

### Fixed

- Preparacao para deploy sem depender do PC local.

### Removed

- Dependencia de caminhos fixos para banco em producao.

## v0.4.1 - Build do executavel na raiz

### Added

- `build_lifeos.ps1`.
- `build_lifeos.bat`.
- Copia versionada em `executables/`.

### Changed

- Build passa a deixar `LifeOS.exe` na pasta principal.

### Fixed

- Processo manual de encontrar executavel apos build.

### Removed

- Nada removido.

## v0.4.0 - Integracao Telegram

### Added

- `backend/services/telegram_bot.py`.
- Integracao com `python-telegram-bot`.
- Tabelas `mobile_entries`, `expenses`, `body_metrics`, `mood_logs`, `task_entries`.
- Endpoints `/telegram/status` e `/telegram/entries`.
- Dashboard com status do bot e registros recentes.

### Changed

- Flask passa a iniciar o bot em thread separada.

### Fixed

- Entrada movel sem abrir dashboard.

### Removed

- Nada removido.

## v0.3.0 - Sistema vivo em tempo real

### Added

- Captura real de atividade consolidada por janela/app.
- Troca de contexto.
- Recalculo automatico de focus score.
- Estado `flow`, `normal` e `disperso`.
- Missao principal recalculada automaticamente.

### Changed

- `/life-status` passou a retornar atividade atual, apps dominantes e timestamp.
- Interface passou a atualizar sem clique manual.

### Fixed

- Dependencia do botao "Capturar agora" para atualizar estado.

### Removed

- Nada removido.

## v0.2.1 - Correcao do executavel

### Added

- Templates no `.spec` do PyInstaller.

### Changed

- Flask passou a rodar no mesmo processo do executavel.

### Fixed

- Loop infinito de paginas ao abrir `LifeOS.exe`.

### Removed

- Uso de `subprocess` com `sys.executable` no inicializador empacotado.

## v0.2.0 - Tarefas e rastreamento continuo

### Added

- CRUD completo de tarefas.
- Rastreador de atividade iniciado junto com Flask.
- Endpoint `/tracker-status`.
- Snapshot `versions/v0.2.0`.

### Changed

- Sistema passou a decidir continuamente.

### Fixed

- Necessidade de captura manual para atualizar estado.

### Removed

- Nada removido.

## v0.1.0 - Nucleo de foco e atividade

### Added

- Rastreamento inicial de janela ativa.
- Logs de atividade.
- Calculo de foco.
- Estados `flow`, `normal`, `disperso`.
- Endpoint `/life-status`.
- Missao automatica inicial.

### Changed

- Primeira estrutura modular do backend.

### Fixed

- Nao aplicavel.

### Removed

- Nao aplicavel.
