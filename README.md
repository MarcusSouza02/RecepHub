# RecepHub

PWA pessoal para gestão de recepções laboratoriais. Monorepo com Next.js, FastAPI e PostgreSQL.

## Sprint 01

Fundação técnica: página provisória responsiva, indicador de disponibilidade da API e do banco,
manifest e ícones PWA, API versionada, SQLAlchemy, Alembic, Docker Compose e CI.
Não há autenticação, cadastros, tabelas de negócio, escalas ou integração com IA nesta etapa.
O ambiente é destinado ao desenvolvimento local, com dados fictícios.

O [relatório técnico detalhado da Sprint 01](docs/08-sprint-01-relatorio-tecnico.md) reúne
o inventário de arquivos, as decisões de implementação, os testes realizados, as limitações
da validação e a preparação para a Sprint 02. Os resultados são históricos; os comandos
documentados permitem reproduzi-los.

## Executar com Docker

Pré-requisitos: Docker Desktop com engine Linux e Docker Compose v2. No Windows, mantenha
o Docker Desktop em execução. Não é necessário instalar Node.js, Python ou PostgreSQL no host.

Na raiz do projeto:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Em Linux/macOS, use `cp .env.example .env`. O Compose também inicia sem `.env`, usando
os mesmos valores fictícios locais do exemplo. Nunca reutilize esses valores em produção.

| Serviço | Endereço |
|---|---|
| Frontend | http://localhost:3000 |
| API (processo ativo) | http://localhost:8000/health |
| API + PostgreSQL | http://localhost:8000/api/v1/health/ready |
| Swagger | http://localhost:8000/docs |

O indicador da página consulta a API pelo navegador. `NEXT_PUBLIC_API_URL` deve ser um endereço
acessível pelo navegador, e não o nome interno `backend`. Dentro do Docker, a API usa
`postgres:5432`. O banco não publica porta no host; frontend e API escutam apenas em `127.0.0.1`.

```sh
docker compose ps
docker compose logs -f
docker compose down
```

`down` preserva o volume do banco. `docker compose down --volumes` apaga os dados locais e os
volumes de dependências/cache: use apenas quando quiser reiniciar o ambiente do zero.

## Desenvolvimento

O código do frontend e os diretórios Python são montados por volumes para atualização durante
desenvolvimento. As dependências e o cache do Next.js ficam em volumes próprios do container.
Depois de alterar dependências, reconstrua as imagens. Para atualizar também o volume de
dependências do frontend sem apagar o banco:

```sh
docker compose up --build -d
docker compose exec frontend npm ci
docker compose restart frontend
```

Se a observação de arquivos falhar no Windows/OneDrive, tente trabalhar em uma pasta local fora
da sincronização. Para o Uvicorn, é possível usar temporariamente `--reload --reload-delay 1`.
Não ativamos polling global sem necessidade observada.

## Verificações

Com os serviços em execução:

```sh
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend pytest -m "not integration"
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
```

Execute o build em container separado para não disputar o cache com o servidor de desenvolvimento:

```sh
docker compose run --rm --no-deps -v /app/.next frontend npm run build
```

Para executar os testes de integração sem usar o banco de desenvolvimento, veja
[o procedimento de validação](docs/07-sprint-01.md). A CI cria PostgreSQL descartável e executa
todos os testes, Alembic, lint, formatação, typecheck, build, detecção de segredos com Gitleaks
e smoke tests do Compose. A action do Gitleaks funciona sem chave de licença em conta pessoal;
se o repositório for transferido para uma organização, reveja a configuração/licença.

## Alembic

```sh
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check
```

Ainda não existem revisões nem tabelas de domínio. O Alembic pode criar sua tabela técnica
`alembic_version`. Para a primeira entidade futura, importe seus modelos em `alembic/env.py`
antes de executar `alembic revision --autogenerate -m "descricao"`. Revise o arquivo gerado
e aplique com `alembic upgrade head`. A API não executa `create_all` nem migrações no startup.

## Execução sem Docker dos aplicativos

Node.js 24 e Python 3.11. O PostgreSQL deve estar acessível separadamente. O `.env` é lido
pelo Compose na raiz; para iniciar o backend a partir de sua pasta, configure as variáveis
no shell ou crie `backend/.env` local ignorado. Configure `POSTGRES_HOST`, `POSTGRES_PORT`,
`POSTGRES_DB`, `POSTGRES_USER` e `POSTGRES_PASSWORD` para essa instância.

```powershell
python -m venv backend/.venv
backend/.venv/Scripts/python -m pip install -r backend/requirements.lock
cd backend
.venv/Scripts/python -m uvicorn app.main:app --reload
```

Em outro terminal:

```sh
cd frontend
npm ci
npm run dev
```

Use `NEXT_PUBLIC_API_URL` no shell ou em `frontend/.env.local` se precisar mudar a URL pública
da API. Variáveis `NEXT_PUBLIC_*` são públicas e incorporadas no build: nunca coloque segredos nelas.

## Estrutura e dependências

- `frontend/src/app`: páginas, layout e manifest; `components/ui`: componente shadcn/ui adaptado.
- `frontend/src/features`: comportamento da interface; `services`: comunicação HTTP.
- `backend/app/api`: endpoints; `core`: configuração e erros; `database`: engine/sessões/base.
- `models`, `schemas`, `services`, `repositories`, `integrations`: responsabilidades do monólito,
  preenchidas conforme surgirem necessidades. Não há abstrações genéricas de negócio.
- `infra`: Dockerfiles de desenvolvimento; `.github/workflows`: verificações automatizadas.
- `docs`: planejamento, requisitos e decisões.

Pydantic Settings valida configuração; psycopg é o driver PostgreSQL; httpx suporta TestClient.
Ruff e pytest verificam o backend. Tailwind/PostCSS cuidam dos estilos; `clsx` e `tailwind-merge`
compõem classes do componente shadcn/ui. Não há dependência de IA, autenticação ou serviço pago.
As versões resolvidas estão em `requirements.lock` e `package-lock.json`. Atualize dependências
intencionalmente e execute novamente as verificações. Os Dockerfiles incluem ferramentas de
desenvolvimento e não constituem configuração de produção.

O ESLint permanece em 9.39.5 porque os plugins React/acessibilidade usados pela configuração
do Next.js ainda restringem a compatibilidade à série 9. A instalação informa fim de suporte
do ESLint 9; acompanhar a atualização desses plugins antes de migrar para a série 10.

## Segurança e PWA

Arquivos `.env`, ambientes virtuais, dumps e dependências são ignorados. Dados reais e segredos
não devem ser adicionados ao Git. CORS permite somente as origens configuradas, sem credenciais.
O `/health` não exige banco; prontidão consulta `SELECT 1` e retorna `503` sem expor erros internos.

O manifest e os ícones provisórios preparam a instalação em navegadores compatíveis. Não há
service worker, cache offline ou push. A instalação ainda precisa de homologação nos dispositivos
utilizados; produção exige HTTPS. Acesso por celular na rede local exige uma configuração
explícita de endereços, portas e CORS.

Os planos de hospedagem serão reavaliados no deploy. A licença do projeto permanece pendente
de escolha da pessoa autora. Fontes oficiais consultadas: [Next.js](https://nextjs.org/docs/app/getting-started/installation),
[Tailwind](https://tailwindcss.com/docs/installation/using-postcss) e
[shadcn/ui](https://ui.shadcn.com/docs/components/card). O componente adaptado mantém a atribuição
em [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
