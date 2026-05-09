# PROJECT CONTEXT - LIFE OS

Este arquivo e a memoria permanente do projeto. Ele deve permitir que outro contexto do Codex, Google AI Studio ou qualquer IA entenda rapidamente o estado real do LIFE OS e continue o desenvolvimento sem recomecar do zero.

## Visao do produto

LIFE OS e um assistente pessoal operacional. Ele existe para decidir o que o usuario deve fazer agora, com base em contexto, energia, foco, historico, tarefas, registros moveis e situacao financeira.

O produto nao deve evoluir como um dashboard passivo. A interface mostra dados, mas a funcao central e decisao.

## Filosofia

O sistema deve reduzir carga mental. Sempre que possivel, ele deve substituir perguntas como:

- O que eu deveria fazer agora?
- Esse gasto cabe no mes?
- Estou em foco ou disperso?
- Minha energia permite tarefa pesada?
- Esse registro precisa virar acao?

por respostas operacionais:

- Missao atual.
- Recomendacao de foco.
- Limite financeiro do dia.
- Alerta contextual.
- Sugestao automatica.

## Conceito central

```text
INPUTS -> PROCESSAMENTO -> DECISAO -> ACAO
```

Inputs:

- Janela ativa no Windows.
- Tarefas cadastradas.
- Transacoes financeiras.
- Mensagens Telegram.
- Atalhos Siri/iPhone que enviam mensagens ao Telegram.
- Registros de humor, sono, peso, treino, agenda e notas.

Processamento:

- Classificacao de atividade.
- Calculo de foco.
- Parser NLP simples.
- Categorizacao financeira.
- Priorizacao de tarefas.

Decisao:

- Missao atual.
- Estado atual: `flow`, `normal`, `disperso`.
- Recomendacao financeira.
- Recomendacao de foco.
- Alertas inteligentes.

Acao:

- Atualizar dashboard.
- Responder Telegram.
- Registrar historico.
- Preparar futura automacao.

## Estado atual do projeto

O projeto ja possui:

- Backend Flask modular.
- SQLAlchemy com SQLite local e suporte preparado para PostgreSQL via `DATABASE_URL`.
- Rotas separadas por dominio.
- Dashboard HTML + Tailwind.
- Tracker de atividade Windows.
- Background tracker junto com Flask.
- Motor de foco e produtividade.
- CRUD de tarefas.
- Motor de decisao de missao.
- Modulo financeiro.
- Telegram bot.
- Parser NLP baseado em regex, palavras-chave e heuristicas.
- Tabela `raw_entries` para nunca perder mensagens.
- Deploy Render/Railway com Gunicorn.
- Scripts de deploy e build local.
- Snapshots em `versions/`.

## Funcionalidades prontas

### Produtividade

- Captura janela ativa.
- Salva `activity_logs`.
- Detecta troca de contexto.
- Calcula `focus_score`.
- Detecta estado operacional.
- Escolhe missao atual com base em tarefas.

### Tarefas

- CRUD completo.
- Campos: nome, impacto, urgencia, energia necessaria, status.
- Missao automatica usa score da tarefa + estado/foco.

### Financeiro

- Perfil financeiro com renda, renda extra, dia de pagamento, metas.
- Transacoes de receita/despesa.
- Categorias automaticas.
- Resumo mensal.
- Alertas inteligentes.
- Limite diario recomendado.
- Analise de intencao de compra.

### Telegram/Siri

- Bot inicia junto com Flask.
- Mensagens entram como texto livre.
- Siri pode enviar texto ao bot via Atalho do iPhone.
- Backend interpreta e salva.
- Dashboard mostra ultimos registros, debug e NLP.

### NLP

Classifica mensagens em:

- `financeiro`
- `saude`
- `humor`
- `produtividade`
- `agenda`
- `treino`
- `nota_geral`

Extrai:

- Numeros.
- Datas relativas simples.
- Horarios.
- Valores monetarios.
- Categoria financeira.
- Sentimento simples.

## Funcionalidades em desenvolvimento

- Revisao manual de `raw_entries`.
- Integracao real com calendario.
- Persistencia PostgreSQL em producao.
- Autenticacao.
- Modulo completo de treino.
- Modulo de saude/habitos.
- Camada IA externa para melhorar NLP.

## Regras importantes do projeto

- Nunca hardcodar token.
- Usar `TELEGRAM_BOT_TOKEN`.
- Manter Flask pronto para Gunicorn.
- Nao usar `debug=True` em producao.
- Manter separacao entre routes, services, models e engine.
- Toda mensagem de Telegram/Siri deve ser salva.
- Se o parser nao entender, salvar como `raw_input`.
- O dashboard deve orientar decisao, nao apenas exibir dados.
- Render deve atualizar quando houver push no GitHub.

## Padroes de UX

Estilo desejado:

- SaaS moderno.
- Dark mode elegante.
- Cards objetivos.
- Sidebar.
- Header simples.
- Status claros.
- Pouco texto explicativo dentro do app.
- Interface focada em decisao.

O dashboard principal deve priorizar:

- Foco atual.
- Missao atual.
- Saude financeira.
- Gasto do mes.
- Saldo previsto.
- Recomendacao do dia.
- Telegram/NLP.

## Padroes tecnicos

- `backend/routes`: apenas HTTP, input/output e orquestracao leve.
- `backend/services`: regras de negocio.
- `backend/models.py`: modelos SQLAlchemy.
- `backend/engine`: integracoes com sistema operacional.
- `frontend/templates`: HTML Jinja.
- Evitar libs desnecessarias.
- Preferir funcoes pequenas e testaveis.
- Manter compatibilidade com cloud Linux e Windows local.

## Problemas conhecidos

- SQLite em Render pode ser efemero sem disco persistente.
- Sem autenticacao; URL publica exposta deve ser tratada com cuidado.
- Telegram usa polling; com mais de um worker Gunicorn pode duplicar bot.
- Sem Alembic; migracoes atuais sao leves e manuais.
- Parser legado ainda existe em `telegram_bot.py` e pode ser removido depois que NLP estabilizar.
- Tracker Windows nao roda na nuvem Linux.

## Decisoes arquiteturais tomadas

- Flask foi mantido pela simplicidade inicial.
- SQLAlchemy foi usado para permitir SQLite agora e PostgreSQL depois.
- Telegram roda em thread separada para nao travar Flask.
- NLP simples fica em `nlp_service.py` para permitir troca futura por IA.
- `raw_entries` garante que nenhuma entrada seja perdida.
- Financeiro usa `transactions` como fonte principal para dashboards.
- `expenses` foi mantida por compatibilidade com parser antigo.
- Render/Gunicorn e o caminho padrao de producao.

## Como o parser NLP deve funcionar

1. Toda mensagem recebida e normalizada.
2. Dados comuns sao extraidos: numeros, datas, horarios, valores e sentimento.
3. Classificadores heuristicas tentam identificar o dominio.
4. A melhor classificacao e aplicada.
5. A entrada original sempre e salva em `raw_entries`.
6. Se interpretada, cria registros estruturados.
7. Se nao interpretada, fica como `raw_input`.
8. Telegram responde com interpretacao e sugestao.
9. Dashboard exibe interpretadas, nao classificadas e sugestoes.

## Prioridades futuras

1. Persistencia real em PostgreSQL.
2. Autenticacao simples.
3. Tela para revisar e transformar `raw_entries`.
4. IA externa opcional para NLP.
5. Modulo agenda com calendario.
6. Modulo treino com plano, carga e historico.
7. Modulo habitos/saude.
8. Testes automatizados.
9. Observabilidade de producao.

## Visao de produto

LIFE OS deve se tornar uma camada operacional pessoal. A interface nao deve perguntar demais. Ela deve observar, interpretar, decidir e orientar.

Frase guia:

```text
Como esse sistema pode decidir no lugar do usuario?
```
