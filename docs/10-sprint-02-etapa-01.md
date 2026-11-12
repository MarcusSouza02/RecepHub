# Sprint 02 — Etapa 1: persistência e migrações

Data: 04/11/2026. Estado: **implementada, em revisão**. Cards S02-01, S02-02 e S02-03.

## 1. Entrega e limites

A etapa entrega a estrutura PostgreSQL da conta única e de suas sessões. Não entrega
login, endpoints, geração de tokens, hash Argon2id funcional ou interface. Nenhuma conta
efetiva foi provisionada. As credenciais de `.env` e a alteração preexistente de
`.env.example` foram preservadas. Nenhuma dependência foi acrescentada.

A migração foi aplicada somente ao banco descartável `recephub_sprint02_test`. O banco
de desenvolvimento não recebeu upgrade/downgrade nesta entrega; o antigo
`recephub-test-db` não foi reutilizado nem removido. Iniciar o Docker Desktop reativou
os containers de desenvolvimento que já tinham política de reinício.

## 2. Arquivos e responsabilidades

| Arquivo | Alteração e motivo |
|---|---|
| `backend/app/models/user.py` | Conta única, UUID, username canônico/único, campo de hash, atividade, auditoria e campos reservados ao limite de tentativas. Índice único sobre constante impede segunda conta mesmo com a primeira inativa. |
| `backend/app/models/user_session.py` | Sessões independentes, FK com cascade, hash hexadecimal único, timestamps e checks temporais. Não existe coluna para token original. |
| `backend/app/models/__init__.py` | Exporta Base e modelos para registro dos metadados. |
| `backend/alembic/versions/0001_auth_foundation.py` | Primeira revisão, sem antecessora; cria somente duas tabelas, constraints e índices. Downgrade desfaz na ordem das dependências. Sem seed. |
| `backend/alembic/env.py` | Carrega os modelos; permite conexão externa para comandos programáticos em testes; compara tipos no modo online. Execução normal continua usando settings. |
| `backend/alembic.ini` | Declara `path_separator = os`, eliminando aviso legado do Alembic. |
| `backend/tests/__init__.py` | Torna os utilitários de teste importáveis de forma explícita. |
| `backend/tests/database.py` | Valida URL dedicada, sufixo `_test`, driver PostgreSQL e opt-in de reset; configura Alembic com a conexão do teste. Não recorre às credenciais da aplicação. |
| `backend/tests/conftest.py` | Fixtures de conexão/migração e sessão com rollback externo e savepoints. Recusa tabelas inesperadas ou registros preexistentes antes de migrar. |
| `backend/tests/test_database.py` | Mantém integração de prontidão usando fixture segura; acrescenta testes dos bloqueios de configuração. |
| `backend/tests/test_auth_models.py` | Exercita defaults, UUIDs, conta única ativa/inativa, username, contador, hashes, FK, cascade, múltiplas sessões e horários no PostgreSQL real. |
| `backend/tests/test_auth_migrations.py` | Upgrade, dados fictícios, downgrade e novo upgrade; confirma revisão, tabelas vazias e `alembic check` antes/depois. |
| `.github/workflows/ci.yml` | Aplica migração antes do pytest e habilita reset somente no banco descartável do job. |
| `docs/04-modelagem-banco.md` | Distingue entidades implementadas das propostas; documenta sessões e constraints da conta. |
| `docs/09-sprint-02.md` | Registra evidências e coloca os três cards em revisão. |
| `README.md` | Atualiza situação do Alembic e aponta o procedimento atual de testes. |
| Este relatório | Reúne execução, resultados, conceitos e preparação da revisão. |

README, roadmap e quadro já continham mudanças do planejamento anterior. A alteração
local de `.env.example` é preexistente e não faz parte desta implementação.

## 3. Conceitos e fluxo

Os modelos descrevem o esquema desejado em SQLAlchemy; Alembic registra a evolução
reproduzível do banco. Importar os modelos não cria tabelas. `upgrade head` executa a
migração; `alembic check` compara o banco com os metadados e detecta diferenças pendentes.

Uma conta possui várias sessões. Excluir a conta remove suas sessões por FK no próprio
PostgreSQL, inclusive sem carregar a coleção no ORM. Constraints protegem escritas que
não passam pelo futuro serviço. O índice sobre `true` faz todas as contas disputarem a
mesma chave, impondo o limite de uma conta.

UUIDs são gerados pela aplicação; timestamps têm fuso e defaults no banco quando
previstos. O banco verifica formato do hash da sessão, mas ainda não calcula SHA-256,
não autentica e não verifica a passagem das 12 horas/2 horas de inatividade. Os valores
de hash de senha dos testes são marcadores fictícios, sem capacidade de login.

## 4. Reprodução dos testes

Use Docker Desktop Linux. Na raiz, crie recursos exclusivos; os nomes abaixo não devem
identificar recursos existentes com dados. Todos os valores são fictícios e só para teste.

```powershell
docker network create recephub-sprint02-tests
docker run -d --name recephub-sprint02-test-db --network recephub-sprint02-tests --tmpfs /var/lib/postgresql/data -e POSTGRES_DB=recephub_sprint02_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only postgres:17-bookworm
docker exec recephub-sprint02-test-db pg_isready -U recephub_test -d recephub_sprint02_test
```

Espere o banco aceitar conexões. Se a imagem do backend não existir, construa-a com
`docker compose build backend`. O comando executado nesta entrega foi:

```powershell
docker run --rm --network recephub-sprint02-tests --mount "type=bind,source=$PWD\backend,target=/app,readonly" -e TEST_DATABASE_URL=postgresql+psycopg://recephub_test:ci-fictional-only@recephub-sprint02-test-db:5432/recephub_sprint02_test -e TEST_DATABASE_ALLOW_RESET=1 recephub-backend:latest python -m pytest -p no:cacheprovider
```

A imagem existente foi reutilizada; o código atual foi montado somente para leitura.
O teste de migração faz downgrade com dados fictícios e termina novamente em `head`,
sem registros. Os testes de modelos isolam os dados por transações revertidas.
Nome de banco e opt-in são barreiras adicionais: quem configurar a URL continua
responsável por apontar exclusivamente para um banco descartável.

Verificações locais adicionais:

```powershell
.\backend\.venv\Scripts\python.exe -m ruff check backend
.\backend\.venv\Scripts\python.exe -m ruff format --check backend
.\backend\.venv\Scripts\python.exe -m pytest backend/tests -m "not integration" -p no:cacheprovider
```

Após a revisão, para aplicar ao desenvolvimento conscientemente:

```powershell
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check
```

Esses três comandos não foram executados contra desenvolvimento nesta entrega. Não
execute downgrade nesse banco para repetir a experiência descartável.

## 5. Evidências e limitações

- 23 testes sem integração passaram no Windows/Python 3.11.9.
- 65 testes passaram no Linux/Python 3.11.18, incluindo 42 testes de integração em PostgreSQL 17.
- Upgrade → downgrade → upgrade e comparação de metadados passaram no teste automatizado.
- Ruff check e formatação passaram, com 29 arquivos Python verificados.
- Aviso conhecido do TestClient/httpx: depreciação na dependência. Sem alteração de dependências nesta etapa.
- O aviso inicial de `path_separator` do Alembic foi corrigido e a suíte repetida.
- Resultado final da repetição: **65 passed, 1 warning em 6,04 segundos**.
- `git diff --check` passou; Git apenas informou a normalização CRLF/LF do documento de modelagem.
- CI remota, frontend e navegador não foram executados nesta etapa de persistência.

O tmpfs não preserva dados após parar o container. Os recursos descartáveis são separados
dos recursos de desenvolvimento; sua remoção manual deve usar somente os nomes desta seção.
O container `recephub-sprint02-test-db` e a rede `recephub-sprint02-tests` foram mantidos
disponíveis para revisão; o banco terminou sem contas ou sessões de teste.

## 6. Diffs relevantes para revisão

```diff
+ Index("uq_users_single_account", text("(true)"), unique=True)
+ ForeignKey("users.id", ondelete="CASCADE")
+ CheckConstraint("expires_at > created_at", name="expires_after_creation")
+ Session(bind=connection, join_transaction_mode="create_savepoint")
```

Na CI, `alembic upgrade head` passou para antes de `pytest`; `TEST_DATABASE_ALLOW_RESET`
é explícito no job. No Alembic, testes fornecem uma conexão já validada, evitando que
o ambiente consulte o banco configurado para a aplicação.

## 7. Revisão e próxima etapa

Sugestão de commit: `feat(auth): add user and session persistence`.
Sugestão de PR para `dev`: **Sprint 02 — Persistência da conta e sessões**. Descrever as
duas entidades, migração, garantias PostgreSQL e os 65 testes, registrando que o banco
de desenvolvimento ainda não foi migrado. Nenhuma operação de branch/commit/push/merge
foi executada.

Após aprovação da Etapa 1 e autorização explícita da Etapa 2, implementar Argon2id,
provisionamento administrativo e endpoints de autenticação conforme S02-04–06.
Os campos e relacionamentos estão preparados; contas reais continuam sendo criadas
manualmente pela pessoa responsável quando esse procedimento existir.
