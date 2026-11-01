# RecepHub — Relatório técnico da Sprint 01

**Sprint:** 01 — Fundação e estrutura arquitetural  
**Versão deste relatório:** 1.0  
**Data de consolidação:** 31/10/2026  
**Finalidade:** explicar a entrega e fornecer a base técnica para preparar a Sprint 02.

Este relatório complementa o [registro original da sprint](07-sprint-01.md). Descreve os arquivos
conferidos no repositório e os resultados observados durante a implementação. Os testes históricos
não foram reexecutados para produzir esta documentação. Um serviço ativo no encerramento daquela
execução pode ter sido parado desde então; a disponibilidade atual precisa ser conferida.

## Sumário

1. [Objetivo, escopo e resultado](#1-objetivo-escopo-e-resultado)
2. [Organização e decisões arquiteturais](#2-organização-e-decisões-arquiteturais)
3. [Inventário completo de arquivos](#3-inventário-completo-de-arquivos)
4. [Funcionamento do backend](#4-funcionamento-do-backend)
5. [Funcionamento do frontend e do PWA](#5-funcionamento-do-frontend-e-do-pwa)
6. [Docker, rede, volumes e ambiente](#6-docker-rede-volumes-e-ambiente)
7. [Dependências e versões registradas](#7-dependências-e-versões-registradas)
8. [Testes e verificações realizados](#8-testes-e-verificações-realizados)
9. [Integração contínua](#9-integração-contínua)
10. [Procedimentos de reprodução](#10-procedimentos-de-reprodução)
11. [Problemas encontrados e ajustes](#11-problemas-encontrados-e-ajustes)
12. [Critérios de aceite e limites da evidência](#12-critérios-de-aceite-e-limites-da-evidência)
13. [Preparação para a Sprint 02](#13-preparação-para-a-sprint-02)
14. [Fontes e controle documental](#14-fontes-e-controle-documental)

## 1. Objetivo, escopo e resultado

A Sprint 01 criou a base de desenvolvimento antes das funcionalidades operacionais. O resultado
é um monorepo com Next.js, FastAPI e PostgreSQL conectados, iniciados por Docker Compose, com
configuração de ambiente, verificações de qualidade e documentação.

### 1.1 Entregas implementadas

- Página provisória identificada como RecepHub, com layout adaptável e componente compartilhado.
- Indicador que consulta disponibilidade da API e do banco, com carregamento, falha e nova tentativa.
- Estrutura inicial PWA: manifest, metadados e dois ícones provisórios.
- API com fábrica de aplicação, ciclo de vida, rotas versionadas, CORS e erros básicos.
- Endpoints distintos para saúde da API e prontidão com PostgreSQL.
- SQLAlchemy síncrono, psycopg, base declarativa e sessões por requisição.
- Alembic preparado, sem entidades de negócio ou migrações artificiais.
- Containers de desenvolvimento, volumes, rede interna e health checks.
- pytest, Ruff, ESLint, TypeScript, build e workflow de GitHub Actions.
- Documentação organizada, exemplo de ambiente, exclusões do Git e instruções de execução.

### 1.2 O que permaneceu fora da sprint

Não foram implementados login/logout, hash de senha, sessão, proteção de rotas, cadastros de
unidades ou colaboradoras, férias/ausências, geração/publicação de escalas, exportação, IA,
Outlook ou envio de mensagens. Não há seed de negócio nem dados reais.

A modelagem propõe seis tabelas futuras, mas elas **não existem no código da Sprint 01**.
Na validação, o banco descartável terminou apenas com a tabela técnica `alembic_version`.

### 1.3 Relação com o roadmap

A sprint entrega parte do **Marco 1 — Fundação**, que também prevê autenticação e uma aplicação
protegida por login. O marco não foi concluído integralmente. O recorte aprovado adiou login e
antecipou a estrutura inicial do PWA prevista no Marco 6.

Este relatório não aprova o escopo da Sprint 02. A seção 13 propõe uma sequência para discussão,
sem autorizar funcionalidades nem definir regras de negócio pendentes.

## 2. Organização e decisões arquiteturais

### 2.1 Estrutura entregue

```text
RecepHub/
├── .github/workflows/ci.yml
├── .env.example
├── .gitattributes
├── .gitignore
├── AGENTS.md
├── README.md
├── THIRD_PARTY_NOTICES.md
├── compose.yaml
├── docs/
│   ├── 01-visao-do-produto.md
│   ├── 02-requisitos.md
│   ├── 03-regras-de-negocio.md
│   ├── 04-modelagem-banco.md
│   ├── 05-arquitetura.md
│   ├── 06-roadmap.md
│   ├── 07-sprint-01.md
│   └── 08-sprint-01-relatorio-tecnico.md
├── infra/
│   ├── backend.Dockerfile
│   └── frontend.Dockerfile
├── backend/
│   ├── .dockerignore
│   ├── pyproject.toml
│   ├── requirements.lock
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   ├── script.py.mako
│   │   └── versions/.gitkeep
│   ├── app/
│   │   ├── main.py
│   │   ├── api/
│   │   │   ├── health.py
│   │   │   └── v1/router.py
│   │   ├── core/{config.py,errors.py}
│   │   ├── database/{base.py,session.py}
│   │   ├── schemas/health.py
│   │   ├── models/
│   │   ├── services/
│   │   ├── repositories/
│   │   └── integrations/
│   └── tests/{conftest.py,test_health.py,test_database.py}
└── frontend/
    ├── .dockerignore
    ├── package.json
    ├── package-lock.json
    ├── tsconfig.json
    ├── next-env.d.ts
    ├── next.config.ts
    ├── eslint.config.mjs
    ├── postcss.config.mjs
    ├── components.json
    ├── public/icons/{icon-192.png,icon-512.png}
    └── src/
        ├── app/{layout.tsx,page.tsx,globals.css,manifest.ts}
        ├── components/ui/card.tsx
        ├── features/system-status/api-status.tsx
        ├── services/api.ts
        └── lib/utils.ts
```

A notação `{arquivo1,arquivo2}` agrupa arquivos do mesmo diretório. Os `__init__.py` estão
enumerados na seção 3; diretórios gerados, como ambientes virtuais e caches, foram omitidos.
O documento 08 foi acrescentado nesta consolidação, depois da implementação da sprint.

### 2.2 Comunicação entre as camadas

```mermaid
flowchart LR
    N[Navegador] -->|HTTP localhost:3000| F[Next.js: HTML, estilos e JavaScript]
    N -->|GET localhost:8000/api/v1/health/ready| B[FastAPI]
    B -->|SQLAlchemy + psycopg: postgres:5432| P[(PostgreSQL)]
```

O JavaScript do indicador executa **no navegador**, portanto usa a URL pública
`http://localhost:8000`, não `http://backend:8000`. O nome `postgres` é resolvido pela API
na rede Docker. Não há proxy de mesma origem nesta entrega.

### 2.3 Decisões e consequências

| Decisão | Justificativa e consequência |
|---|---|
| Monorepo simples | Aplicativos, documentação e infraestrutura evoluem juntos, sem gerenciador adicional de monorepo. |
| Monólito modular no backend | Uma API e um banco atendem ao uso inicial, sem microsserviços, filas ou orquestradores extras. |
| SQLAlchemy síncrono | Simplifica sessões e testes; não foi demonstrada necessidade de persistência assíncrona. |
| Camadas de negócio inicialmente vazias | Evita interfaces e repositórios genéricos sem uso concreto. |
| Saúde separada de prontidão | Distingue API ativa de capacidade de consultar o banco; melhora diagnóstico e inicialização. |
| Migrações explícitas | Não há `create_all` ou migração automática no startup; alterações de esquema passarão por revisão. |
| Lockfiles | Registram versões resolvidas. As imagens Docker permanecem por tags, sem digest fixado no código. |
| PWA online | Prepara manifest/ícones sem adicionar cache de dados, offline ou biblioteca específica. |
| Exposição local | Frontend e API publicam portas em loopback; PostgreSQL permanece interno. |

## 3. Inventário completo de arquivos

Arquivos preexistentes são identificados como preservados ou movidos. Não houve commit de
encerramento para estabelecer uma comparação por SHA. As descrições refletem os arquivos
conferidos e o histórico da implementação.

### 3.1 Raiz e infraestrutura

| Arquivo | O que foi feito e para que serve |
|---|---|
| `AGENTS.md` | Preexistente e preservado. Orienta leitura de requisitos, simplicidade, testes críticos e proteção de credenciais. |
| `README.md` | Criado com instalação, URLs, Docker, verificações, migrações, execução fora do Docker, dependências e limitações. Nesta consolidação recebeu link para o relatório detalhado. |
| `.env.example` | Criado com variáveis e valores fictícios locais; não contém segredos reais. |
| `.gitignore` | Exclui `.env` e variantes, ambientes virtuais, caches Python, compilados, cobertura, metadados de pacote, `node_modules`, `.next`, exportações, logs, IDEs e `backups/`; preserva `.env.example`. Não detecta universalmente dumps ou segredos em outros caminhos. |
| `.gitattributes` | Normaliza texto em LF e trata PNG como binário, reduzindo diferenças Windows/Linux. |
| `compose.yaml` | Define projeto `recephub`, serviços, builds, ambiente, portas, volumes, dependências e health checks. Permite `docker compose up --build` na raiz. |
| `infra/backend.Dockerfile` | Python 3.11 slim, instalação do lock, usuário `appuser` UID 10001, cópia com proprietário correto e `/app` gravável por esse usuário; Uvicorn com reload na porta 8000. |
| `infra/frontend.Dockerfile` | Node 24 Bookworm slim, `npm ci`, usuário `node`, `.next` criado com permissões adequadas e `npm run dev` na porta 3000. Desativa telemetria do Next.js. |
| `.github/workflows/ci.yml` | Quatro jobs: segredos, backend, frontend e Compose. Detalhados na seção 9. |
| `THIRD_PARTY_NOTICES.md` | Origem e licença MIT do Card adaptado de shadcn/ui. A licença geral do projeto permanece pendente. |

### 3.2 Documentação

| Arquivo | Alteração realizada |
|---|---|
| `docs/01-visao-do-produto.md` | Movido da raiz. Alinhado para incluir IA opcional no MVP completo, após o núcleo operacional: objetivo correspondente, introdução da seção 7 e situação da seção 9.7. |
| `docs/02-requisitos.md` | Movido para `docs/`, preservando requisitos. Não representa funcionalidades já entregues. |
| `docs/03-regras-de-negocio.md` | Movido, preservando regras e seus estados de validação; essas regras não foram implementadas nesta sprint. |
| `docs/04-modelagem-banco.md` | Movido, mantendo a proposta de seis tabelas futuras e decisões pendentes; não gerou tabelas de domínio. |
| `docs/05-arquitetura.md` | Movido, preservando arquitetura de evolução. Seu desenho completo ultrapassa o escopo já implementado. |
| `docs/06-roadmap.md` | Movido; recebeu o recorte aprovado da sprint e marcações de frontend, backend, estrutura/testes e CI configurada. Login, licença e publicação GitHub não foram considerados concluídos. |
| `docs/07-sprint-01.md` | Criado na implementação com decisões, comandos, resultados e limitações. Preservado como registro original; nesta consolidação recebeu link para este relatório e indicação de resultados históricos. |
| `docs/08-sprint-01-relatorio-tecnico.md` | Criado em 31/10/2026: inventário detalhado, fluxos, testes, evidências, riscos e preparação da Sprint 02. |

O alinhamento corrigiu a visão anterior, que colocava IA após o MVP, enquanto requisitos,
arquitetura e roadmap mais recentes a incluíam no MVP completo. Também distinguiu a Sprint 01
do Marco 1 inteiro. Jornadas, treinamento, cobertura e exportação de rascunhos continuam
pendentes; a reorganização não definiu regras operacionais novas.

### 3.3 Backend: configuração, API e persistência

| Arquivo | Implementação e responsabilidade |
|---|---|
| `backend/pyproject.toml` | Pacote `recephub-backend` 0.1.0, Python mínimo 3.11, dependências, descoberta apenas de `app*`, build setuptools e configuração de pytest/Ruff. |
| `backend/requirements.lock` | Versões exatas resolvidas com Python 3.11, incluindo transitivas e ferramentas de desenvolvimento. Sem referência local do pacote editável. |
| `backend/.dockerignore` | Exclui ambiente virtual, caches, `.env` e metadados de instalação do contexto de build. |
| `backend/app/main.py` | `create_app(settings=None)` e `app`; FastAPI, lifespan, engine em `app.state`, descarte no encerramento, CORS, erros e routers. Swagger/OpenAPI disponíveis. |
| `backend/app/core/config.py` | `Settings`, ambiente/`.env`, validação de porta e origens CORS, URL SQLAlchemy por `URL.create` e settings com cache `lru_cache`. |
| `backend/app/core/errors.py` | Handler de exceções inesperadas: HTTP 500 genérico e log somente do nome do tipo da exceção, sem mensagem potencialmente sensível. |
| `backend/app/database/base.py` | Base declarativa e convenção de nomes para índices, unicidade, checks, chaves estrangeiras e primárias. Sem entidades de domínio. |
| `backend/app/database/session.py` | Engine com `pool_pre_ping`, timeout de conexão de 3 s e `statement_timeout` de 3000 ms; sessão por requisição com `yield` e fechamento por contexto. Não faz commit automático. |
| `backend/app/api/health.py` | Routers de saúde/prontidão; consulta `SELECT 1` e converte `SQLAlchemyError` em HTTP 503 sem detalhes internos. |
| `backend/app/api/v1/router.py` | Agrupa a prontidão sob `/api/v1`; `/health` fica fora do prefixo por ser endpoint de infraestrutura. |
| `backend/app/schemas/health.py` | Contratos Pydantic `HealthResponse` e `ReadyResponse`, com literais `status="ok"` e `database="ok"`. |
| `backend/alembic.ini` | Localização dos scripts e caminho de importação; não contém URL/senha do banco. |
| `backend/alembic/env.py` | Reutiliza settings/engine e `Base.metadata`, configura online/offline, compara tipos e encerra engine. O modo online foi validado; não há validação histórica específica do modo offline. |
| `backend/alembic/script.py.mako` | Template de revisões futuras: identificadores, relações entre revisões e funções `upgrade`/`downgrade`. Não é uma revisão aplicada. |
| `backend/alembic/versions/.gitkeep` | Mantém o diretório de revisões vazio no versionamento. Não cria tabelas nem representa revisão Alembic. |

### 3.4 Pacotes Python preparados

Os arquivos abaixo foram criados vazios. Delimitam pacotes, sem regras de negócio, importação
automática de entidades ou abstrações genéricas.

| Arquivo | Papel reservado |
|---|---|
| `backend/app/__init__.py` | Pacote principal. |
| `backend/app/api/__init__.py` | Endpoints. |
| `backend/app/api/v1/__init__.py` | Versão inicial da API. |
| `backend/app/core/__init__.py` | Configuração e preocupações transversais. |
| `backend/app/database/__init__.py` | Infraestrutura de persistência. |
| `backend/app/models/__init__.py` | Entidades ORM futuras; sem modelos nesta entrega. |
| `backend/app/schemas/__init__.py` | Contratos; os de saúde estão em `health.py`. |
| `backend/app/services/__init__.py` | Casos de uso e regras futuras. |
| `backend/app/repositories/__init__.py` | Consultas/persistência de negócio quando necessárias. |
| `backend/app/integrations/__init__.py` | Adaptadores externos futuros; sem IA ou e-mail implementados. |

### 3.5 Backend: testes

| Arquivo | Implementação |
|---|---|
| `backend/tests/conftest.py` | Fixture `client`, aplicação por teste com `Settings(_env_file=None)` e lifespan por TestClient. Evita ler `.env`; variáveis de processo ainda podem ser consideradas pelos settings. |
| `backend/tests/test_health.py` | Oito funções, uma parametrizada em três entradas: dez casos de saúde, prontidão com mock, erros, CORS, settings e documentação. |
| `backend/tests/test_database.py` | Um teste `integration`, condicionado a `TEST_DATABASE_URL`; PostgreSQL real, `SELECT 1`, override da sessão e consulta de prontidão. Encerra a engine ao final. |

### 3.6 Frontend: ferramentas e configuração

| Arquivo | Implementação |
|---|---|
| `frontend/package.json` | Projeto privado 0.1.0; scripts `dev`, `build`, `start`, `lint`, `typecheck`; versões diretas fixadas e Node `>=24 <25`. `dev`/`start` escutam `0.0.0.0` dentro do container. |
| `frontend/package-lock.json` | Árvore resolvida e integridades npm, utilizada por `npm ci`; inclui pacotes opcionais conforme plataforma. |
| `frontend/tsconfig.json` | TypeScript estrito, resolução `bundler`, integração Next.js, JSX, compilação incremental sem emissão, alias `@/*` para `src/*` e tipos gerados em `.next`. |
| `frontend/next-env.d.ts` | Declarações administradas pelo Next.js. Referências de rotas podem variar entre desenvolvimento/build; não editar manualmente. |
| `frontend/next.config.ts` | Configuração mínima com `poweredByHeader: false`; sem proxy de API ou service worker. |
| `frontend/eslint.config.mjs` | Flat config com Next Core Web Vitals e TypeScript; ignora `.next`, `out`, `next-env.d.ts`. O script falha se houver avisos. |
| `frontend/postcss.config.mjs` | Ativa `@tailwindcss/postcss`, exportando variável `config` para evitar aviso de exportação anônima. |
| `frontend/components.json` | Prepara shadcn/ui: `new-york`, TypeScript, React Server Components, CSS variables e aliases. Alias de hooks declarado, sem pasta criada sem uso. |
| `frontend/.dockerignore` | Exclui dependências locais, build/cache, `.env`, logs e estado incremental do contexto de build. |

### 3.7 Frontend: aplicação e recursos

| Arquivo | Implementação |
|---|---|
| `frontend/src/app/layout.tsx` | Layout raiz `pt-BR`, CSS global, título/descrição, nome da aplicação, metadados Apple e cor do tema. |
| `frontend/src/app/page.tsx` | Marca, identificação de desenvolvimento, apresentação e cartão de conexão; grade adaptável e cabeçalho com `flex-wrap`. Sem telas funcionais. |
| `frontend/src/app/globals.css` | Tailwind 4, tokens de cores, tema e fonte do sistema; reduz animações/transições com `prefers-reduced-motion`. |
| `frontend/src/app/manifest.ts` | Gera `/manifest.webmanifest`: nome, descrição, idioma, escopo, URL inicial, `standalone`, cores e ícones. |
| `frontend/public/icons/icon-192.png` | PNG provisório 192×192, letra R sobre verde. Gerado localmente com System.Drawing, sem dependência de geração de imagens por IA. |
| `frontend/public/icons/icon-512.png` | Variante 512×512. Os dois ícones usam propósito `any`; sem ícone maskable específico. |
| `frontend/src/components/ui/card.tsx` | Adaptação shadcn/ui: `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`; props nativas, `data-slot` e classes combináveis. |
| `frontend/src/lib/utils.ts` | `cn` combina classes condicionais com `clsx` e resolve conflitos Tailwind com `tailwind-merge`. |
| `frontend/src/services/api.ts` | URL e `checkApi(signal)` centralizados; fetch sem cache, validação HTTP/JSON e do contrato de saúde. |
| `frontend/src/features/system-status/api-status.tsx` | Client Component com estados, timeout de 8 s, cancelamento, proteção após desmontagem, mensagens acessíveis e nova tentativa. |

### 3.8 Artefatos locais e gerados

A implementação inicializou um repositório Git local e criou `.env` a partir do exemplo fictício.
Não houve commit, push, criação remota de repositório ou deploy na Sprint 01.

`backend/.venv`, metadados da instalação editável, `__pycache__`, caches Ruff/pytest,
`frontend/node_modules`, `.next` e `*.tsbuildinfo` são gerados e ignorados. Não precisam ser
copiados para outra máquina: podem ser regenerados. `.git` contém metadados locais, não aplicação.

No Docker foram criados rede, volumes, containers de desenvolvimento, containers temporários
de verificação e o PostgreSQL separado `recephub-test-db`. Este último foi preservado no
encerramento histórico porque a remoção foi rejeitada; o estado atual não foi consultado nesta tarefa.

## 4. Funcionamento do backend

### 4.1 Inicialização e sessões

1. `main.py` expõe `app`, usada por `uvicorn app.main:app`.
2. `create_app` usa settings fornecidos ou obtidos por `get_settings`.
3. No lifespan, cria engine em `app.state.engine`.
4. `get_session` abre sessão por requisição que precise do banco.
5. O contexto fecha a sessão ao final; escritas futuras precisarão de commit/rollback explícitos.
6. No encerramento, `engine.dispose()` libera o pool.

Criar a engine não comprova conexão. A prova ocorre na consulta real de prontidão.
`pool_pre_ping` verifica conexões reutilizadas do pool.

### 4.2 Contratos HTTP entregues

| Método/caminho | Sucesso | Falha ou limite |
|---|---|---|
| `GET /health` | `200`, `{"status":"ok"}` | Não consulta banco nem comprova saúde de todas as dependências. |
| `GET /api/v1/health/ready` | `200`, `{"status":"ok","database":"ok"}` | Erro SQLAlchemy: `503`, `{"detail":"Banco de dados indisponível"}`. |
| `GET /docs` | `200`, Swagger | Gerado pelo FastAPI, sem login nesta sprint. |
| `GET /openapi.json` | Especificação da API | Teste confirma inclusão da rota de prontidão. |

Exceções inesperadas recebem `500`, `{"detail":"Erro interno do servidor"}`. Não há catálogo
de erros de domínio. Respostas padrão do FastAPI, como validação e rota inexistente, continuam
disponíveis; somente os cenários descritos nos testes têm evidência específica registrada.

### 4.3 Configuração e segurança atual

Settings lê ambiente e `.env` relativo à pasta de execução e ignora campos extras. A porta
aceita 1–65535. Origens CORS exigem HTTP/HTTPS e autoridade, sem caminho, query, fragmento
ou credenciais; wildcard global `*` é rejeitado.

O middleware permite origens configuradas, método `GET`, cabeçalhos `Accept`/`Content-Type`
e `allow_credentials=False`. CORS controla o navegador: **não substitui autenticação nem
impede um cliente HTTP de chamar uma API acessível**. Login e escritas exigirão revisão de
métodos, credenciais e proteção CSRF apropriada.

Não existem conta, cookie, hash, CSRF, rate limiting ou autorização de negócio implementados.
O fuso operacional dos documentos ainda não corresponde a um subsistema de datas entregue:
não há datas de escala nem campos de auditoria de domínio nesta sprint.

### 4.4 Alembic e a primeira migração futura

O modo online usa settings/engine da aplicação. `upgrade head` pode criar `alembic_version`
sem revisão de domínio. Nesse estado, `current` pode não exibir identificador de revisão,
porque ainda não existe revisão criada. `check` não encontrou novas operações, coerente com
metadados vazios e ausência de tabelas de negócio.

Antes da primeira migração real, será necessário importar modelos para preencher `Base.metadata`,
gerar/revisar a revisão, aplicar em banco descartável e testar constraints/rollback. A validação
sem revisões comprovou infraestrutura, **não** um ciclo real de criação/alteração de tabelas.

A convenção de check constraints usa `constraint_name`: checks futuros devem receber nome
explícito. O timeout de consulta de 3 s também afeta a engine do Alembic e deverá ser reavaliado
se uma migração legítima precisar de mais tempo.

## 5. Funcionamento do frontend e do PWA

### 5.1 Consulta de disponibilidade

1. A página renderiza cartão e `ApiStatus`.
2. Após montagem no navegador, o efeito cria `AbortController` e chama `checkApi`.
3. O serviço usa `NEXT_PUBLIC_API_URL`, com fallback `http://localhost:8000`, remove uma barra
   final e consulta `/api/v1/health/ready` com `cache: "no-store"`.
4. Exige sucesso HTTP e JSON objeto com `status` e `database` iguais a `ok`.
5. Sucesso muda para `online`; erro HTTP/rede/JSON/contrato ou timeout muda para `offline`.
6. O botão incrementa a tentativa, refaz a consulta e fica desabilitado durante carregamento.
7. A limpeza do efeito cancela a requisição, limpa timer e impede atualização após desmontagem.

| Estado | Mensagem |
|---|---|
| `loading` | Verificando conexão… |
| `online` | API e banco de dados disponíveis |
| `offline` | Não foi possível conectar ao sistema |

Não há polling periódico. O resultado retrata a última consulta; depois de uma mudança de
disponibilidade, é preciso clicar no botão ou recarregar. O limite de 8 s pertence ao componente;
o serviço recebe o sinal de cancelamento e não define sozinho esse timeout.

### 5.2 Interface e acessibilidade preparadas

O layout usa fonte de sistema, cores compartilhadas, limites de largura e espaçamentos adaptáveis.
O cabeçalho quebra linha. O status combina texto e cor, usa `role="status"`/`aria-live="polite"`
e ponto decorativo com `aria-hidden`. Há foco visível no botão e respeito a movimento reduzido.
Esses recursos estão no código, mas não substituem testes visuais, teclado ou leitor de tela,
que não tiveram homologação registrada.

### 5.3 Limites da entrega PWA

Manifest, ícones, metadados e apresentação adaptável estão preparados. Não há service worker,
cache offline, push ou garantia de instalação em todos os dispositivos. O manifest usa `/`
como `start_url`/`scope`, `display: "standalone"` e `pt-BR`.

Produção exige HTTPS e homologação de instalação no dispositivo escolhido. Os ícones são
provisórios e não representam identidade visual final aprovada.

## 6. Docker, rede, volumes e ambiente

### 6.1 Serviços e portas

| Serviço | Imagem/base | Porta no host | Comunicação |
|---|---|---|---|
| `postgres` | `postgres:17-bookworm` | Nenhuma | API usa `postgres:5432`. |
| `backend` | `python:3.11-slim` | `127.0.0.1:8000` | Uvicorn escuta `0.0.0.0:8000` dentro do container. |
| `frontend` | `node:24-bookworm-slim` | `127.0.0.1:3000` | Next.js escuta `0.0.0.0:3000` dentro do container. |

`5432/tcp` na listagem Docker é porta interna, não publicação no host. A rede padrão permite
resolução dos nomes de serviço. Acesso pelo celular exige configuração deliberada de endereços,
portas, CORS e contexto seguro; loopback atende somente ao computador local.

### 6.2 Volumes e persistência

| Volume/montagem | Finalidade |
|---|---|
| `postgres_data` → `/var/lib/postgresql/data` | Preservar banco entre recriações de containers. |
| `./backend/app`, `tests`, `alembic` | Código, testes e revisões para desenvolvimento/comandos no container. |
| `alembic.ini` e `pyproject.toml` | Configurações do backend montadas como somente leitura. |
| `./frontend` → `/app` | Código do frontend para desenvolvimento. |
| `frontend_node_modules` → `/app/node_modules` | Separar dependências Linux das instaladas no Windows. |
| `frontend_next` → `/app/.next` | Cache de desenvolvimento no Docker. |

Os nomes efetivos normalmente recebem prefixo `recephub_`. `docker compose down` preserva
volumes; `down --volumes` apaga banco e caches/dependências desses volumes. Rebuild não atualiza
necessariamente o volume persistente de `node_modules`: nesse caso, executar `npm ci` no serviço
e reiniciá-lo, conforme README. As imagens são de desenvolvimento, não de produção.

### 6.3 Inicialização e health checks

| Serviço | Verificação | Intervalo / timeout / tentativas / tolerância inicial |
|---|---|---|
| PostgreSQL | `pg_isready` com usuário/banco configurados | 5 s / 3 s / 10 / 10 s |
| Backend | HTTP `/api/v1/health/ready` | 10 s / 6 s / 5 / 10 s; requisição interna limitada a 5 s |
| Frontend | Fetch HTTP da página inicial | 15 s / 10 s / 5 / 45 s |

A API depende de PostgreSQL saudável, e o frontend depende de API saudável. Isso ordena a
subida inicial. Não há política de restart configurada nem garantia de recuperação automática
ou interrupção em cascata caso uma dependência falhe depois.

### 6.4 Variáveis de ambiente

| Variável | Uso e padrão local |
|---|---|
| `POSTGRES_DB` | `recephub`, injetado no PostgreSQL e na API. |
| `POSTGRES_USER` | Usuário fictício `recephub`, compartilhado por banco/API. |
| `POSTGRES_PASSWORD` | Exemplo fictício `local-development-only` no Compose; exclusivo local. Settings sem Compose tem senha vazia por padrão. |
| `POSTGRES_HOST` | Compose define `postgres`; settings fora do Docker usa `localhost`. |
| `POSTGRES_PORT` | `5432`, validada pelos settings. |
| `CORS_ORIGINS` | Lista JSON com `http://localhost:3000` e `http://127.0.0.1:3000`. |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000`, acessível pelo navegador; pública e incorporada ao build. |
| `NEXT_TELEMETRY_DISABLED` | `1` no Docker e nos jobs do frontend. |
| `TEST_DATABASE_URL` | URL de banco descartável para o teste de integração; não configura engine normal ou Alembic. |

Host/porta do banco são definidos pelo Compose e não constam do exemplo da raiz. O Compose
também inicia com defaults fictícios sem `.env`. Fora dele, a leitura de `.env` depende da pasta
de execução. `.dockerignore` impede copiar esses arquivos para as imagens. Não colocar segredos
em `NEXT_PUBLIC_*` nem reutilizar a senha fictícia em produção.

## 7. Dependências e versões registradas

Versões abaixo são as encontradas na entrega, não recomendações de versões atuais. Atualizações
devem ser intencionais, compatíveis e acompanhadas de nova validação.

### 7.1 Frontend

| Dependência | Versão | Finalidade |
|---|---|---|
| Next.js | 16.4.3 | App Router, servidor, build, manifest e tipos de rotas. |
| React / React DOM | 19.3.1 | Componentes e interação no navegador. |
| Tailwind / plugin PostCSS | 4.3.3 | Utilitários de estilo e processamento CSS. |
| TypeScript | 6.0.3 | Verificação de tipos. |
| ESLint | 9.39.5 | Lint, com avisos tratados como falha pelo script. |
| eslint-config-next | 16.4.3 | Regras Next.js/React/TypeScript. |
| clsx | 2.1.1 | Classes condicionais. |
| tailwind-merge | 3.7.0 | Resolução de conflitos de classes. |
| @types/node | 24.19.2 | Tipos Node. |
| @types/react / @types/react-dom | 19.3.0 | Tipos React. |

shadcn/ui foi preparado por configuração e componente adaptado, sem pacote monolítico de UI.
Não foram adicionados estado global, biblioteca de consultas, biblioteca PWA ou SDK de IA.

### 7.2 Backend

| Dependência | Versão no lock | Finalidade |
|---|---|---|
| FastAPI | 0.162.0 | API, dependências e OpenAPI. |
| Uvicorn | 0.54.0 | Servidor ASGI. |
| Pydantic / Pydantic Settings | 2.14.2 / 2.16.2 | Contratos e configuração validada. |
| SQLAlchemy | 2.1.6 | Engine, sessões e base ORM. |
| psycopg / psycopg-binary | 3.3.6 | Driver PostgreSQL sem compilação local obrigatória. |
| Alembic | 1.20.1 | Migrações. |
| pytest | 9.2.0 | Testes automatizados. |
| httpx | 0.28.1 | Suporte ao TestClient atual. |
| Ruff | 0.17.3 | Lint, imports e formatação. |

`pyproject.toml` declara faixas; `requirements.lock` fixa a resolução usada nas imagens e CI.
O lock também contém transitivas como Starlette 1.10.0, Pydantic Core, AnyIO, Mako, httpcore,
certificados e utilitários. Elas não representam novas funcionalidades implementadas.

Ruff usa alvo Python 3.11, linha de 100 caracteres e regras `E`, `F`, `I`, `UP`, `B`.
A exceção `B008` está limitada a `app/api/health.py` pelo uso de `Depends` do FastAPI.

## 8. Testes e verificações realizados

### 8.1 Resultado histórico consolidado

| Verificação | Ambiente e resultado observado |
|---|---|
| Backend unitário | Windows/Python 3.11.9: dez passaram; integração excluída por marcador. |
| Backend completo | Linux/Python 3.11.18 em container: onze passaram, incluindo PostgreSQL real descartável. |
| Ruff | Lint/formatação passaram no host e no container; Linux registrou 22 arquivos já formatados. |
| Frontend lint | Passou com zero avisos após correção do PostCSS e retorno ao ESLint compatível. |
| Frontend typecheck | `next typegen` e `tsc --noEmit` passaram. |
| Frontend build | Passou no host e em container isolado; gerou `/`, `/_not-found` e `/manifest.webmanifest`. |
| Compose | Configuração validada; `up --build -d --wait --wait-timeout 180` terminou com três serviços saudáveis. |
| HTTP no computador local | Página em 3000; `/health`, `/api/v1/health/ready` e `/docs` em 8000: HTTP 200. |
| Manifest e ícones | HTTP 200, nome `RecepHub` e PNGs 192×192/512×512 conferidos programaticamente. |
| Conteúdo HTML | `RecepHub` e `Conexão do sistema` presentes na resposta da página. |
| CORS real | Prontidão retornou `Access-Control-Allow-Origin: http://localhost:3000` para essa origem. |
| Alembic | `upgrade head`, `current`, `check` sem erro; mensagem final: `No new upgrade operations detected.` |
| Banco de teste | Consulta `\dt` mostrou somente `public.alembic_version`. |
| Git ignore | `.env`, `.venv`, `node_modules` e `.next` confirmados como ignorados. |
| npm | Instalação final e `npm ci` Linux informaram zero vulnerabilidades naquela consulta, sem garantia permanente. |

### 8.2 Os dez casos de saúde e configuração

Todos estão em `backend/tests/test_health.py`. Sessões simuladas são substituídas por
`dependency_overrides`, sem PostgreSQL nesses casos.

| Função/caso | Verificação efetiva |
|---|---|
| `test_health_does_not_require_database` | `/health`: 200 e exatamente `{"status":"ok"}`, sem consulta ao banco. |
| `test_ready_queries_database` | Prontidão: 200, contrato correto e execução de `SELECT 1` na sessão mockada. |
| `test_ready_hides_database_error` | `OperationalError` simulado: 503 genérico; o texto `secret` não aparece no corpo. |
| `test_cors_allows_only_configured_origin` | Origem local recebe cabeçalho de permissão; `https://untrusted.example` não recebe. Não equivale a bloquear sua requisição HTTP no servidor. |
| `test_cors_preflight_rejects_write_method` | Preflight POST para origem local retorna 400, conforme métodos atuais. |
| `test_settings_reject_unsafe_origins` — `*` | Wildcard global gera erro de validação. |
| Mesmo teste — `https://example.com/path` | Origem contendo caminho é rejeitada. |
| Mesmo teste — `file://example` | Esquema não HTTP/HTTPS é rejeitado. |
| `test_docs_and_openapi_available` | Swagger 200 e OpenAPI contendo `/api/v1/health/ready`. |
| `test_unexpected_error_is_sanitized` | Rota temporária somente no app de teste lança `RuntimeError`; TestClient recebe 500 genérico. A rota não pertence à aplicação entregue. |

Há oito funções nesse arquivo; a parametrização gera três casos no teste de settings, totalizando
dez. Esses testes não comprovam regras futuras de jornada, ausência ou publicação.

### 8.3 O caso de integração com PostgreSQL real

`test_postgres_connection_and_ready`, em `backend/tests/test_database.py`, foi executado contra
`recephub-test-db`, separado do banco de desenvolvimento.

Cria engine para `TEST_DATABASE_URL`, confirma que `SELECT 1` retorna 1, fornece sessões por
override e consulta o JSON de prontidão por TestClient. Não cria modelos, não insere dados de
pessoas/unidades nem executa Alembic. Migrações foram verificadas por comandos separados.
Sem a variável, o caso é **ignorado (skip)**: `pytest` sem ela não comprova integração real.
Na execução completa registrada, a variável estava configurada.

### 8.4 O que não foi testado ou não pode ser concluído

- Não houve teste de componente React, navegador automatizado ou E2E.
- O host de automação de navegador estava indisponível; não há screenshot de homologação.
- Fetch no navegador, botão, timeout e acessibilidade não tiveram validação interativa registrada.
- Build/typecheck/HTTP não comprovam ausência de overflow ou instalação PWA em celular.
- Falha de banco foi simulada por mock; não há registro de interrupção real do PostgreSQL para esse teste.
- Não houve medição de cobertura percentual, carga, concorrência, desempenho ou backup/restore.
- Gitleaks está configurado, mas sua execução remota não foi observada.
- Produção, cookies, autenticação e dados reais não foram validados; esses recursos não existem na entrega.

## 9. Integração contínua

O workflow `Quality` dispara em push/pull request com permissão global `contents: read`.
Foi configurado, mas nenhum run remoto foi executado durante a sprint.

| Job | Etapas configuradas |
|---|---|
| `secrets` | Checkout com histórico completo, Gitleaks v3, token automático do GitHub e comentários em PR desativados. Sem chave pessoal no arquivo. |
| `backend` | PostgreSQL 17 temporário, health check, Python 3.11, cache pip pelo lock, instalação, Ruff, pytest e três comandos Alembic. |
| `frontend` | Node 24, cache npm pelo lock, `npm ci`, lint, geração/verificação de tipos e build. |
| `compose` | Valida configuração, constrói/sobe aguardando saúde, consulta endpoints por curl, mostra logs em falha e encerra com volumes no runner descartável. |

São usados checkout v6, setup-python/setup-node v6 e Gitleaks v3. O banco da CI tem valores
fictícios e publica 5432 para acesso pelo runner; isso não altera o Compose local sem porta de banco.

A varredura de segredos depende da primeira execução remota. A configuração da action considera
conta pessoal; eventual transferência para organização exige revisão de licença/configuração,
conforme README. Workflow presente não equivale a pipeline remoto aprovado.

## 10. Procedimentos de reprodução

Os comandos são instruções para uma nova execução, não evidência de execução nesta revisão
documental. Parta da raiz do projeto, salvo indicação em contrário.

### 10.1 Iniciar e inspecionar

Docker Desktop deve estar ativo com engine Linux e Compose v2. Para o fluxo Docker, não é
necessário instalar Node/Python no host. Copie o exemplo somente se ainda não houver seu `.env`:

```powershell
Copy-Item .env.example .env
docker compose up --build
```

Em outro terminal:

```sh
docker compose ps
docker compose logs -f backend frontend
```

Abra `http://localhost:3000`, `http://localhost:8000/health`,
`http://localhost:8000/api/v1/health/ready` e `http://localhost:8000/docs`.
Para execução fora do Docker, consulte o [README](../README.md#execução-sem-docker-dos-aplicativos).

### 10.2 Verificações sem banco de teste

```sh
docker compose exec backend ruff check .
docker compose exec backend ruff format --check .
docker compose exec backend pytest -m "not integration"
docker compose exec frontend npm run lint
docker compose exec frontend npm run typecheck
```

Build com cache isolado do servidor de desenvolvimento:

```sh
docker compose run --rm --no-deps -v /app/.next frontend sh -c 'npm run lint && npm run typecheck && npm run build'
```

O volume anônimo em `/app/.next` evita disputar o cache ativo. Registre separadamente quaisquer
warnings de dependências, além do código de saída das verificações.

### 10.3 Integração e Alembic em banco descartável

Primeiro confira se já existe o container de teste, que foi preservado na execução anterior.
Não tente recriá-lo ou apagá-lo sem conferir sua finalidade atual:

```sh
docker ps -a --filter name=recephub-test-db
docker compose up -d postgres
```

Se o nome estiver livre, crie o banco temporário:

```sh
docker run --detach --name recephub-test-db --network recephub_default -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only -e POSTGRES_DB=recephub_test postgres:17-bookworm
docker exec recephub-test-db pg_isready -U recephub_test -d recephub_test
```

Após aceitar conexões, com imagem do backend previamente construída:

```sh
docker compose run --rm --no-deps -e TEST_DATABASE_URL=postgresql+psycopg://recephub_test:ci-fictional-only@recephub-test-db:5432/recephub_test backend pytest
docker compose run --rm --no-deps -e POSTGRES_HOST=recephub-test-db -e POSTGRES_DB=recephub_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only backend alembic upgrade head
docker compose run --rm --no-deps -e POSTGRES_HOST=recephub-test-db -e POSTGRES_DB=recephub_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only backend alembic current
docker compose run --rm --no-deps -e POSTGRES_HOST=recephub-test-db -e POSTGRES_DB=recephub_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only backend alembic check
docker exec recephub-test-db psql -U recephub_test -d recephub_test -c '\dt'
```

`TEST_DATABASE_URL` atende ao teste; `POSTGRES_*` dos comandos seguintes aponta Alembic ao mesmo
banco. Se mudar nome do projeto/rede, ajuste `recephub_default`. Quando houver autorização para
descartar esse banco, a limpeza explícita pode ser feita por:

```sh
docker stop recephub-test-db
docker rm -v recephub-test-db
```

Isso remove dados do banco de teste. Documentar o procedimento não revoga a recusa anterior
nem autoriza execução automática. Para parar o ambiente principal preservando dados, use
`docker compose down`, sem `--volumes`.

## 11. Problemas encontrados e ajustes

| Ocorrência durante a implementação | Tratamento e situação final |
|---|---|
| Docker instalado, daemon inativo | Docker Desktop iniciado; engine Linux disponível para builds/testes. |
| Downloads bloqueados no sandbox | Instalações/acesso ao Docker ocorreram após solicitações apropriadas, sem contornar bloqueios. |
| Instalação editável descobria `app` e `alembic` | Descoberta limitada a `app*` e build setuptools declarado; instalação concluída. |
| Instalação/escrita lentas no workspace OneDrive | Execução prosseguiu até concluir; não se alterou sincronização global ou ativou polling indiscriminado. A causa exata não foi medida. |
| Aviso ESLint na exportação PostCSS | Exportação passou a usar variável `config`; lint final sem avisos de código. |
| ESLint 9 fora de suporte | Série 10 avaliada, com conflitos de peers React/acessibilidade; retorno à 9.39.5 compatível, sem forçar peers. Limitação registrada. |
| Cache pytest sem permissão | `/app` passou a pertencer a `appuser`; nova execução dos onze testes eliminou esse aviso. |
| Permissões de cache Next.js | `.next` criado pelo usuário `node` antes do volume; fluxo final de desenvolvimento/build funcionou. |
| Cabeçalho em tela estreita | `flex-wrap` adicionado; intenção responsiva implementada, sem homologação visual. |
| Depreciação no TestClient | Starlette indicou migração futura para `httpx2`; testes finais passaram com um aviso, sem filtro global para ocultá-lo. |
| Aviso npm sobre script de `unrs-resolver` | Observado no build; lint/typecheck/build Linux passaram. Não houve aprovação genérica de scripts de instalação. |
| Git com proprietário diferente entre usuário e sandbox | Consultas usaram `safe.directory` por comando; sem alteração de confiança global. |
| Navegador automatizado indisponível | Limitação registrada, sem tratar HTTP/build como validação visual. |
| Remoção do banco temporário rejeitada | Container preservado; sem tentativa alternativa de remoção. |

Nenhum ajuste implementou ou modificou regras operacionais de colaboradoras/escalas.

## 12. Critérios de aceite e limites da evidência

| Critério original | Situação no encerramento da implementação |
|---|---|
| 1. Projeto iniciar por Compose | Atendido: build/subida e três serviços saudáveis. |
| 2. Frontend em `localhost:3000` | HTTP 200 e HTML confirmados; inspeção visual pendente. |
| 3. Backend em `localhost:8000/health` | Atendido: 200 e contrato automatizado. |
| 4. Swagger em `/docs` | Atendido: 200 e teste de documentação/OpenAPI. |
| 5. Conexão backend–PostgreSQL | Atendido: prontidão real, `SELECT 1` e integração. |
| 6. Frontend consultar backend | Serviço/componente implementados; contrato/CORS validados. Fetch interativo no navegador não observado: homologação ponta a ponta parcial. |
| 7. Alembic funcional | Atendido para infraestrutura sem revisões; ciclo de migração real fica para a primeira entidade. |
| 8. Testes/verificações sem erros | Atendido nas verificações descritas, com warnings documentados. CI remota/E2E não executados. |
| 9. README com instalação/execução | Atendido; complementado por este relatório. |

A fundação foi entregue com essas ressalvas. Isso não conclui o MVP, a autenticação do Marco 1,
a homologação PWA ou a liberação para produção/dados reais.

## 13. Preparação para a Sprint 02

### 13.1 Base que pode ser reutilizada

A próxima sprint pode aproveitar fábrica da aplicação, `/api/v1`, settings, engine/sessões,
base declarativa, Alembic, organização de componentes/features/serviços, tokens visuais e CI
configurada. Não precisa recriar o scaffold. Ainda precisará implementar entidades, regras e
interfaces do recorte aprovado; pacotes vazios não são funcionalidades prontas.

### 13.2 Pendências técnicas para triagem

| Momento | Item | Próxima verificação sugerida |
|---|---|---|
| Antes de homologar interface | Navegador, indicador e PWA | Estados, nova tentativa, teclado, telas estreitas/largas e instalação nos dispositivos escolhidos. |
| Antes de confiar na CI | GitHub/primeiro workflow | Definir remoto/licença, observar quatro jobs e corrigir falhas reais do runner. |
| Antes de funcionalidade privada | Autenticação | Concluir RF-01 conforme arquitetura/recorte aprovado e proteger endpoints de negócio. |
| Antes da primeira tabela | Modelos/migração | Importar entidades no Alembic, gerar/revisar revisão, testar constraints, aplicação/rollback em banco descartável. |
| Ao preparar login/escritas | CORS e HTTP | Rever métodos, cookies/credenciais, CSRF e erros do cliente. Hoje há só GET e nenhuma credencial. |
| Ao adicionar consultas de negócio | Timeouts/transações | Rever limite de 3 s para consultas/migrações e definir commit/rollback por caso de uso. |
| Manutenção de ferramentas | ESLint/peers e TestClient | Reavaliar compatibilidade sem ocultar avisos ou forçar dependências. |
| Organização local | Banco temporário preservado | Conferir estado/finalidade atual; descarte depende de autorização apropriada. |
| Antes de deploy/uso real | Segurança e dados | HTTPS, autenticação validada, backup/restore e autorização de dados reais ainda não entregues. |

### 13.3 Questões de produto preservadas

| Tema | Pergunta antes do módulo correspondente |
|---|---|
| Jornadas | Dias, horários, intervalos, sábados e eventual passagem por meia-noite? |
| Horas previstas | Como distinguir soma de duração e validação contratual, alinhando RN-07 e RF-21? |
| Cobertura | Quais mínimos por unidade/faixa? Ausência de regra não pode virar mínimo inferido do quadro habitual. |
| Treinamento | Quando é posto/atividade e quando impede outra alocação? A modelagem contém proposta, não validação final. |
| Publicação | Como editar dia publicado e identificar versão enviada sem histórico avançado? |
| Exportação | Permitir rascunho ou somente publicado? Documentos ainda precisam de alinhamento explícito. |
| Postos exclusivos | Quais representam posição exclusiva e quando sobreposição deve bloquear? |
| Inativação/histórico | Confirmar efeitos sobre consultas e alocações existentes. |
| Dados reais | Quais autorizações e ambiente privado serão necessários? Desenvolvimento continua fictício. |
| Identidade/licença | Aprovar apresentação/exportação futura e escolher licença geral. |

Essas pendências não impedem toda evolução técnica, mas impedem decisões automáticas de negócio
nos módulos afetados. Os estados de confirmação permanecem nos documentos 01–05.

### 13.4 Proposta de sequência para discussão

Para completar a fundação, uma opção é centrar a Sprint 02 em **autenticação de conta única e
fechamento das pendências de validação**, antes dos cadastros. É proposta, não escopo aprovado:

1. Confirmar objetivo, limites e critérios de aceite da Sprint 02.
2. Revisar `users` e decidir persistência/revogação de sessões; ainda não existe detalhamento
   disso no código, e pode ser necessário ajustar o esquema de forma documentada.
3. Selecionar biblioteca Argon2id e mecanismo de sessão, justificando dependências.
4. Criar primeira entidade/migração e provisionamento administrativo, sem autorregistro.
5. Implementar login/logout e proteção, revendo CORS, cookies e CSRF conforme arquitetura.
6. Criar interface de login e comportamento de sessão no cliente; o serviço atual só cobre saúde.
7. Testar credenciais inválidas, hash, acesso anônimo, expiração/revogação e logout.
8. Homologar navegador, preservar regressão de saúde e observar CI no GitHub.

Se outro recorte for aprovado, o inventário identifica o que reutilizar e o que falta. Cadastros
não devem começar presumindo que autenticação já existe.

### 13.5 Checklist de preparação

- [ ] Ler este relatório e conferir manifests/lockfiles antes de atualizar dependências.
- [ ] Revalidar ambiente local; resultados históricos não garantem serviços ativos hoje.
- [ ] Definir recorte e critérios de aceite da Sprint 02.
- [ ] Priorizar autenticação e validação navegador/CI, ou registrar alternativa aprovada.
- [ ] Resolver regras necessárias ao recorte, preservando as demais como pendentes.
- [ ] Definir migrações e testes com banco descartável.
- [ ] Confirmar responsáveis por validação funcional, licença e remoto GitHub.
- [ ] Atualizar roadmap/documentação conforme decisões efetivamente aprovadas.

## 14. Fontes e controle documental

| Registro | Data | Conteúdo |
|---|---|---|
| Registro original, documento 07 | 29/10/2026 | Decisões, comandos, resultados e limitações da implementação. |
| Relatório detalhado, documento 08 v1.0 | 31/10/2026 | Inventário, fluxos, versões, testes, ajustes, aceite e preparação da Sprint 02. Somente documentação. |

Fontes internas: [visão](01-visao-do-produto.md), [requisitos](02-requisitos.md),
[regras](03-regras-de-negocio.md), [modelagem](04-modelagem-banco.md),
[arquitetura](05-arquitetura.md), [roadmap](06-roadmap.md), [README](../README.md),
[workflow](../.github/workflows/ci.yml), [testes de saúde](../backend/tests/test_health.py),
[teste de banco](../backend/tests/test_database.py), [lock Python](../backend/requirements.lock)
e [manifest npm](../frontend/package.json).

Evidências consolidadas do histórico da implementação e do documento 07. Não foram gerados
JUnit, relatório de cobertura ou screenshots naquela execução. Sem commit de encerramento,
não há fotografia imutável do estado por SHA. Nesta tarefa documental foram conferidos arquivos,
referências e inventário; não se afirma nova aprovação de testes da aplicação.
