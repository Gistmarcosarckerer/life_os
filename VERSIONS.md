# LIFE OS Versions

Este arquivo documenta os snapshots e a evolucao do projeto. Snapshots ficam em `versions/` e servem como ponto de retorno manual.

## Politica de versoes

- Cada atualizacao relevante deve registrar uma entrada neste arquivo.
- Mudancas grandes devem ter snapshot em `versions/vX.Y.Z`.
- O snapshot nao substitui Git; ele e uma rede de seguranca local.
- Para publicar em producao, usar Git/GitHub/Render.

## Snapshots existentes

```text
versions/v0.1.0
versions/v0.2.0
versions/v0.2.1
versions/v0.3.0
versions/v0.4.0
versions/v0.4.1
versions/v0.5.0
versions/v0.6.0
versions/v0.7.0
versions/v0.8.0
versions/v0.9.0
versions/v0.10.0
versions/v0.11.0
versions/v0.12.0
versions/v0.12.1
versions/v0.13.0
```

## v0.13.0 - Dashboard inteligente visual dark

Status: implementado, aguardando publicacao/validacao visual em producao.

Principais mudancas:

- Dashboard principal redesenhado com visual dark premium.
- Entrada inteligente no dashboard para registrar frases naturais.
- API `/api/smart-entry` para interpretar, salvar e aplicar entradas.
- API `/api/summary` para consolidar estado operacional.
- Foto pessoal usada como fundo da tela inicial e foto de perfil.

Observacoes:

- A foto foi copiada para `frontend/static/images/profile-beach-gym.jpeg`.
- Publicar via `deploy_lifeos.bat` para o Render rebuildar automaticamente.

## v0.12.1 - Memoria de ambiente Render

Status: documentacao atualizada.

Principais mudancas:

- Registrado que o Render ja tem as variaveis principais configuradas.
- Valores sensiveis nao foram salvos.
- `PROJECT_CONTEXT.md` e `AI_STUDIO_CONTEXT.md` atualizados para continuidade futura.

Observacoes:

- Essa versao nao altera codigo de runtime.
- Usar esta informacao apenas como contexto; nunca versionar segredos.

## v0.12.0 - Seguranca para dados reais

Status: implementado, exige configuracao de `LIFE_OS_ADMIN_PASSWORD` no Render.

Principais mudancas:

- Login privado.
- Sessao segura.
- CSRF em POST/PUT/PATCH/DELETE.
- Headers de seguranca.
- Webhook Pluggy protegido por segredo.
- Rotas privadas bloqueadas em producao se senha admin estiver ausente.

Observacoes:

- Configure `LIFE_OS_ADMIN_PASSWORD` antes de publicar.
- Atualize o webhook da Pluggy para usar URL gerada pelo app ou inclua `?secret=<PLUGGY_WEBHOOK_SECRET>`.

## v0.11.0 - Inbox inteligente

Status: implementado, pronto para validacao com entradas reais.

Principais mudancas:

- `raw_entries` recebeu campos de revisao.
- Tabela `personal_rules` criada.
- `inbox_service.py` criado.
- Nova pagina `/inbox`.
- APIs `/api/inbox/summary`, `/api/inbox/items`, `/api/inbox/items/<id>/review` e `/api/inbox/rules`.
- Inbox permite confirmar, ignorar, criar transacao, criar tarefa e criar regra pessoal.

Observacoes:

- Migracao leve adiciona colunas novas em SQLite.
- Proximo passo: aplicar `personal_rules` automaticamente no `nlp_service.py`.

## v0.10.0 - Integracao Pluggy/Open Finance

Status: implementado, requer credenciais Pluggy configuradas e validacao com consentimento real.

Principais mudancas:

- `pluggy_service.py` criado.
- Tabelas `bank_connections`, `bank_accounts` e `imported_transactions`.
- Financeiro ganhou botoes para conectar banco e sincronizar transacoes.
- Pluggy Connect Widget integrado via CDN.
- Transacoes importadas entram na tabela `transactions` com `source="pluggy"`.

Observacoes:

- As credenciais devem ficar somente em variaveis de ambiente.
- Como as chaves foram expostas em chat, devem ser rotacionadas no painel da Pluggy antes de uso real.
- Validar em producao se o plano Pluggy permite conectores Open Finance para C6.

## v0.9.0 - Interface inspirada no modelo Centric

Status: alteracao visual pronta para validacao no navegador.

Principais mudancas:

- `base.html` reestilizado com fundo claro, sidebar larga, cards arredondados e acento indigo.
- `dashboard.html` atualizado com cards grandes de metricas no estilo do modelo.
- CSS global ajustado para manter paginas existentes compativeis.

Observacoes:

- A stack Flask/Jinja foi mantida; o app React do modelo foi usado apenas como referencia visual.
- Validar responsividade e contraste apos deploy.

## v0.8.0 - Documentacao de longo prazo

Status: documentacao funcional.

Principais mudancas:

- README profissional reestruturado.
- `PROJECT_CONTEXT.md` criado para memoria permanente.
- `ARCHITECTURE.md` criado para arquitetura tecnica.
- `CHANGELOG.md` criado no padrao Keep a Changelog.
- `AI_STUDIO_CONTEXT.md` criado para Google AI Studio.

Observacoes:

- Esta versao nao altera regra de negocio.
- Serve como base para continuidade entre contextos do Codex e outras IAs.

## v0.7.0 - Parser NLP livre Telegram/Siri

Status: funcional, requer validacao em ambiente com dependencias instaladas.

Principais mudancas:

- `raw_entries` criado para registrar toda mensagem.
- `nlp_service.py` criado.
- Classificacao: financeiro, saude, humor, produtividade, agenda, treino e nota geral.
- Extracao: numeros, datas, horarios, valores, categorias e sentimento.
- Endpoint `/telegram/raw-entries`.
- Dashboard mostra interpretadas, nao classificadas e sugestoes.

Observacoes:

- Mantem parser legado em `telegram_bot.py`; pode ser removido em refatoracao futura.
- Toda mensagem deve ser salva, mesmo sem interpretacao total.

## v0.6.0 - Financeiro profissional e dashboard premium

Status: funcional.

Principais mudancas:

- Modelos financeiros adicionados.
- Dashboard financeiro criado.
- Alertas inteligentes.
- Analise de compra.
- Telegram registra receitas/despesas em `transactions`.
- UI premium com sidebar e cards.

Observacoes:

- SQLite em Render precisa de disco persistente ou migracao PostgreSQL.

## v0.5.0 - Deploy Render/Railway

Status: funcional.

Principais mudancas:

- Gunicorn.
- `Procfile`.
- `render.yaml`.
- `.env.example`.
- `config.py`.
- `/healthz`.
- Preparacao para PostgreSQL.

Observacoes:

- Render deve usar `gunicorn backend.app:app`.
- Tracker Windows deve ficar desligado em cloud Linux.

## v0.4.1 - Build do executavel na raiz

Status: funcional local Windows.

Principais mudancas:

- Scripts de build.
- `LifeOS.exe` na raiz.
- Copia versionada em `executables/`.

## v0.4.0 - Integracao Telegram

Status: funcional.

Principais mudancas:

- Bot Telegram.
- Entradas moveis.
- Tabelas moveis.
- Endpoints de status e registros.

Observacoes:

- Token nunca deve ser versionado.

## v0.3.0 - Sistema vivo em tempo real

Status: funcional local Windows.

Principais mudancas:

- Captura real consolidada.
- Focus score automatico.
- Estado em tempo real.
- Missao automatica.
- Dashboard atualiza sem clique.

## v0.2.1 - Correcao do executavel

Status: funcional.

Principais mudancas:

- Corrigido loop infinito de paginas.
- Flask no mesmo processo do executavel.
- Navegador abre uma unica vez.

## v0.2.0 - Tarefas e rastreamento continuo

Status: funcional.

Principais mudancas:

- CRUD de tarefas.
- Rastreador em background.
- Endpoint `/tracker-status`.

## v0.1.0 - Nucleo inicial

Status: historico.

Principais mudancas:

- Logs de atividade.
- Calculo de foco.
- Estado operacional.
- `/life-status`.
- Missao automatica inicial.

## Como voltar manualmente para uma versao

1. Escolha um snapshot em `versions/`.
2. Copie os arquivos da versao desejada para a raiz do projeto.
3. Rode o sistema localmente.
4. Se estiver correto, publique com:

```powershell
.\deploy_lifeos.bat "rollback para vX.Y.Z"
```

## Observacoes importantes

- `versions/` esta no `.gitignore`; snapshots sao locais.
- Git continua sendo a fonte de deploy para Render.
- Para rollback em producao, preferir rollback pelo Render ou Git quando possivel.
