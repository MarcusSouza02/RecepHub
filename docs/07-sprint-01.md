# Sprint 01 — Fundação

O [relatório técnico detalhado](08-sprint-01-relatorio-tecnico.md) complementa este registro
original com inventário dos arquivos, funcionamento das camadas, casos de teste e preparação
da Sprint 02. Os resultados abaixo são históricos, referentes ao encerramento da implementação.

Plano aprovado: fundação local com frontend Next.js, backend FastAPI e PostgreSQL,
sem autenticação, cadastros, regras de escala ou integração com IA. Esta sprint entrega
parte do Marco 1; login será implementado posteriormente.

## Decisões

- Monorepo e monólito modular, sem microsserviços ou ferramentas de orquestração adicionais.
- SQLAlchemy síncrono + psycopg: simplicidade de sessão e testes para o uso inicial.
- `/health` verifica o processo; `/api/v1/health/ready` verifica PostgreSQL com `SELECT 1`.
- CORS explícito e acesso de desenvolvimento restrito ao host. PostgreSQL sem porta publicada.
- Alembic preparado, sem migrações vazias e sem modelos de domínio.
- Manifest, ícones e layout iniciados nesta sprint; homologação PWA permanece no Marco 6.
- Credenciais do exemplo são fictícias e exclusivas para desenvolvimento. Sem dados reais.
- Camadas de negócio ficam como pacotes sem implementação até haver necessidade concreta.
- CI usa dados fictícios e PostgreSQL descartável; testes unitários não dependem do banco.

## Testes de integração em banco descartável

Com a imagem do backend construída, crie um serviço temporário de teste na rede do Compose:

```sh
docker compose up -d postgres
docker run --detach --name recephub-test-db --network recephub_default -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only -e POSTGRES_DB=recephub_test postgres:17-bookworm
docker exec recephub-test-db pg_isready -U recephub_test -d recephub_test
```

Quando `pg_isready` informar que aceita conexões:

```sh
docker compose run --rm --no-deps -e TEST_DATABASE_URL=postgresql+psycopg://recephub_test:ci-fictional-only@recephub-test-db:5432/recephub_test backend pytest
docker compose run --rm --no-deps -e POSTGRES_HOST=recephub-test-db -e POSTGRES_DB=recephub_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only backend alembic upgrade head
docker compose run --rm --no-deps -e POSTGRES_HOST=recephub-test-db -e POSTGRES_DB=recephub_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only backend alembic current
docker compose run --rm --no-deps -e POSTGRES_HOST=recephub-test-db -e POSTGRES_DB=recephub_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only backend alembic check
docker rm -f -v recephub-test-db
```

O último comando remove exclusivamente o container e os volumes anônimos do banco de teste.

## Pendências preservadas

Jornadas, cobertura, tratamento de treinamento, política de edição após publicação, possibilidade
de exportar rascunhos, autorização para dados reais, licença e hospedagem. Nenhuma dessas regras
foi definida pelo código da fundação.

## Resultado da validação

| Verificação | Resultado |
|---|---|
| Compose com build | PostgreSQL, backend e frontend saudáveis |
| `/`, `/health`, `/api/v1/health/ready`, `/docs` | HTTP 200 pelo computador local |
| Manifest e ícones | HTTP 200; PNGs 192×192 e 512×512 |
| Backend no Linux | 11 testes passaram, incluindo PostgreSQL real descartável |
| Ruff | Lint e formatação passaram no container |
| Alembic | `upgrade head`, `current` e `check` passaram no banco descartável |
| Tabelas | Somente `alembic_version` no banco de teste; sem tabelas de domínio |
| Frontend no Linux | ESLint, typecheck e build passaram em container isolado |
| CORS | Origem local permitida; origem externa e método de escrita rejeitados nos testes |
| Git ignore | `.env`, `.venv`, `node_modules` e `.next` ignorados |

Limitações observadas:

- A inspeção visual no navegador não foi executada: o host de automação de navegador estava
  indisponível. Responsividade, interação do indicador no navegador e instalação PWA em
  dispositivos ainda exigem homologação visual/manual.
- A CI está configurada, mas não foi executada no GitHub; não houve publicação remota.
- O TestClient atual emite aviso de depreciação sobre `httpx`; os testes passam. A migração
  para `httpx2` poderá ser feita em atualização das ferramentas de teste.
- ESLint 9 informa fim de suporte na instalação; a série 10 ainda conflita com os plugins
  React/acessibilidade usados pelo Next.js. Não foram forçadas resoluções incompatíveis.
- O container `recephub-test-db` foi mantido porque a solicitação de remoção foi rejeitada.
  Ele é separado do banco de desenvolvimento e não publica portas.

Os serviços de desenvolvimento foram deixados em execução. Nenhum commit, push ou deploy foi feito.
