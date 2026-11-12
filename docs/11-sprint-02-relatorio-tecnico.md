# Sprint 02 — autenticação e acesso ao sistema

Data: 12/11/2026. Entrega: conta única, sessões, login/logout e dashboard privado inicial.
Estado: validação local aprovada; consolidação da homologação e CI remota em andamento.

## 1. Escopo e coordenação

O usuário autorizou o coordenador a avançar entre as etapas, distribuir subagentes,
revisar, criar commits sem `Co-authored-by` e enviar para `dev`. Essa autorização
substitui os checkpoints manuais do planejamento de 04/11.

| Responsável | Trabalho |
|---|---|
| Etapa 1 | Avaliação das garantias de persistência já publicadas em `e43fa0c`. |
| Etapa 2 | Código e contratos de hash, provisionamento e sessões, integrados pelo coordenador. |
| Etapa 3 | Matriz adversa e testes de autenticação, concorrência e segurança. |
| Etapa 4 | Proxy de mesma origem, guard, formulário, logout e proposta de E2E. |
| Etapa 5 | Revisão de layout, teclado, estado vazio, monitor e cobertura de homologação. |
| Revisão final | Inspeção independente do código por `gpt-6-astra`, com esforço xhigh. |
| Coordenador | Aplicação das alterações, integração, execução dos testes, correções e publicação. |

Parte dos subagentes inicialmente não recebeu ferramentas de workspace; suas propostas
foram aplicadas e verificadas pelo coordenador. O revisor final e o agente da Etapa 5
inspecionaram arquivos reais, em modo somente leitura. Revisão estática não foi
apresentada como execução de testes.

O banco de desenvolvimento não foi migrado ou populado automaticamente. `.env` e a
alteração preexistente de `.env.example` foram preservados. O antigo `recephub-test-db`
não foi reutilizado. Nenhuma conta real, senha padrão ou funcionalidade operacional
de colaboradoras, unidades, escalas ou IA foi criada.

## 2. Fluxo implementado

```mermaid
sequenceDiagram
    participant N as Navegador
    participant X as Next.js
    participant A as FastAPI
    participant P as PostgreSQL
    N->>X: POST login / JSON / Origin / CSRF
    X->>X: Lista restrita, origem, CSRF e limite 4 KiB
    X->>A: Requisição com cabeçalhos permitidos
    A->>P: Reservar tentativa sob bloqueio da conta
    P-->>A: Commit da reserva
    A->>A: Verificar Argon2id
    A->>P: Revalidar conta e hash; persistir SHA-256 da sessão
    A-->>X: Dados públicos + Set-Cookie HttpOnly
    X-->>N: Cookie de sessão e dados públicos
    N->>X: Acesso ao dashboard
    X->>A: Consultar sessão antes de renderizar
    A->>P: Validar conta, revogação e prazos sob bloqueio
    A-->>X: Sessão válida
    X-->>N: Dashboard privado sem cache
```

O token contém 32 bytes aleatórios; somente seu SHA-256 fica no banco. Cookie de 12h,
HttpOnly, SameSite=Lax, Path=/ e sem Domain. Em produção HTTPS, Secure e nome
`__Host-recephub_session`; em desenvolvimento, `recephub_session`.

O backend aplica 12h absolutas e 2h desde a última requisição autenticada. A consulta
de sessão atualiza `last_seen_at` sem prolongar a expiração absoluta. Logout revoga
somente a sessão apresentada; novo login no mesmo navegador substitui a anterior.
Reset administrativo troca o hash e revoga todas as sessões na mesma transação.

Cinco formulários válidos em 15 minutos compartilham a linha da conta no PostgreSQL,
inclusive sucessos e nomes de usuário incorretos. A sexta tentativa recebe 429 com
Retry-After. Recusas não prolongam a janela nem apagam uma sessão existente. Antes
do provisionamento não existe conta/linha para manter esse contador; provisione a
conta antes de disponibilizar o sistema.

O monitor não faz polling. Um timer controla a interface, e foco/visibilidade/histórico
provocam revalidação. Os prazos usam referência HTTP do servidor e `performance.now`,
evitando depender do relógio do dispositivo. O backend continua sendo a autoridade.

## 3. Arquivos do backend

| Arquivo | Conteúdo e finalidade |
|---|---|
| `app/core/security.py` | Argon2id 64 MiB, 3 iterações, paralelismo 1, salt 16 bytes e hash 32 bytes; normalização de username, hash do token e relógio UTC. Hash fictício aleatório para a verificação uniforme de conta desconhecida. |
| `app/core/config.py` | AUTH_ORIGIN exata, cookie seguro e ENVIRONMENT. Produção exige HTTPS e Secure; mantém configuração PostgreSQL existente. |
| `app/services/auth.py` | Provisionamento, reset, login, sessão e logout. Reserva curta de tentativas; revalidação do hash após Argon para um reset concorrente prevalecer; locks na ordem conta → sessão. |
| `app/api/v1/auth.py` | POST login, GET session, POST logout; JSON estrito e validação sanitizada, corpo em streaming limitado a 4 KiB, origem/CSRF exatos e rejeição de cabeçalhos duplicados. Cookies e respostas no-store. |
| `app/api/v1/router.py` | Registro das rotas de autenticação sob `/api/v1`. |
| `app/cli/__init__.py` | Pacote da administração local. |
| `app/cli/auth.py` | `create` e `reset-password`, com getpass e confirmação. Não aceita senha em argumentos. Falha de banco sem imprimir SQL/credenciais. |
| `app/core/errors.py` | Handler reutilizável de AuthError e resposta 503 sanitizada para indisponibilidade PostgreSQL. |
| `app/main.py` | Disponibiliza os settings da instância para validação de origem e cookie, inclusive em testes. |
| `pyproject.toml`, `requirements.lock` | Argon2-cffi e dependências transitivas fixadas. Justificativa: hash de senha resistente com Argon2id, conforme decisão aprovada. |
| `tests/test_auth.py` | Hash, limites, CSRF, corpo, sessão, dispositivos, prazos, contador, usuário inativo, indisponibilidade, guard reutilizável e cookies HTTPS. |
| `tests/test_auth_admin.py` | CLI real com entrada/getpass substituídos no teste, criação, duplicação, reset e revogação; confere ausência de segredo na saída. |
| `tests/test_auth_concurrency.py` | Conexões PostgreSQL reais: seis tentativas concorrentes, reset durante verificação e leitura de sessão concorrente com logout/reset. |
| `tests/e2e_admin.py` | Utilitário exclusivamente de testes, fora das rotas da aplicação. Exige URL `_test` e opt-in; só administra a conta fictícia `e2e.demo`. Prepara, expira ou limpa os dados do navegador. |

Os modelos, a migração e as fixtures da Etapa 1 continuam documentados no
[relatório da persistência](10-sprint-02-etapa-01.md).

## 4. Arquivos do frontend e infraestrutura

| Arquivo | Conteúdo e finalidade |
|---|---|
| `src/lib/auth/config.ts` | Configuração exclusiva do servidor: origem pública, backend interno e nome do cookie. Booleanos compatíveis com a leitura do backend. |
| `src/lib/auth/session.ts` | Validação da sessão no FastAPI antes de renderizar. Cookie não comprova autenticação. Separa 401 de indisponibilidade; valida dados públicos e horário do servidor. |
| `src/app/api/v1/[...path]/route.ts` | Proxy com lista restrita: login/logout POST, sessão/prontidão GET. Destino fixo, timeout, sem redirects upstream; somente cookie e cabeçalhos necessários. Preserva Set-Cookie e Retry-After; limite de corpo durante leitura. |
| `src/app/page.tsx` | Redireciona para login ou dashboard com base na sessão validada. |
| `src/app/login/page.tsx` | Página responsiva de acesso. |
| `src/features/auth/login-form.tsx` | Formulário acessível, bloqueio de envio duplicado, loading e mensagens distintas para credenciais, validação, 429 e falha técnica. |
| `src/features/auth/logout-button.tsx` | Só anuncia saída após revogação confirmada; falha mantém a página e mostra erro. |
| `src/features/auth/session-monitor.tsx` | Timer sem polling, verificação ao retomar, timeout e aviso de indisponibilidade. Navegação completa ao encerrar validade. |
| `src/features/dashboard/private-shell.tsx` | Sidebar desktop, topo mobile, identidade, Dashboard/Sair e link para pular ao conteúdo. |
| `src/app/dashboard/page.tsx` | Guard na própria página, layout privado, estado vazio e indicador de saúde. Sem métricas ou links operacionais fictícios. |
| `src/app/error.tsx` | Indisponibilidade sem apresentar erro interno ou confundir falha técnica com logout. |
| `src/services/api.ts` | Prontidão por URL relativa, sem comunicação direta do navegador com FastAPI. |
| `package.json`, `package-lock.json` | Playwright 1.56.1 fixado e script test:e2e. Justificativa: validar navegador, cookies, navegação e integração reais. Atualizações transitivas compatíveis também foram tentadas para os avisos do audit. |
| `next-env.d.ts` | Tipos gerados pelo Next.js atualizados pelo build/typegen. |
| `playwright.config.ts` | Chromium desktop e mobile, produção Next na porta 3180, API de testes em 3181 e um worker para isolar a conta única. |
| `tests/e2e/auth.spec.ts` | Fluxos reais contra FastAPI/PostgreSQL; falhas 503 da interface são injetadas explicitamente pelo Playwright. |
| `compose.yaml` | Configuração compartilhada de origem/cookie e URL interna de backend. Não altera credenciais existentes. |
| `.github/workflows/ci.yml` | Novo job browser: PostgreSQL descartável, API real, migração, build Next e Chromium desktop/mobile. Demais checks preservados. |
| `.gitignore` | Ignora resultados e relatórios do Playwright. Traces e screenshots automáticos estão desabilitados para evitar capturar campos de senha. |

README, modelagem, arquitetura, roadmap e quadro de cards refletem a entrega. Os
relatórios da Sprint 01 e da Etapa 1 preservam seus resultados históricos.

## 5. Validação observada

| Verificação | Resultado observado |
|---|---|
| Backend completo | 95 testes aprovados em PostgreSQL 17/Python 3.11.18; 31,48 s. |
| Ruff e formatação | Aprovados, 38 arquivos Python na verificação final. |
| ESLint, TypeScript e build Next.js | Aprovados localmente. |
| Navegador real | 22 cenários validados em desktop/mobile. Última rodada completa: 20 aprovados e dois casos com sincronização de foco corrigida; rodada dirigida posterior: quatro aprovados em 27 s, incluindo esses dois casos e relógio. A primeira rodada de 18 casos também passou integralmente. |
| Compose | `docker compose config --quiet` aprovado. |
| Benchmark Argon2id no container | 404,9 / 416,8 / 340,3 ms; média aproximada 387 ms. Não é garantia de desempenho em produção. |
| GitHub da Etapa 1 | Execuções de `e43fa0c` consultadas em 12/11: concluídas com sucesso. |
| GitHub desta entrega | A observar após o push, separadamente dos resultados locais. |

Os cenários de navegador cobrem login/logout, cookie inacessível ao JavaScript, sessão
forjada, duas sessões independentes, Voltar após logout, HTML sem cache, rate limit,
CSRF/proxy, responsividade, teclado, manifest, expiração real no banco e skew de relógio.
O 503 da interface é simulado por interceptação explícita; não é apresentado como queda
real de rede. O backend tem teste de erro PostgreSQL sanitizado e logout sem falso sucesso.

Durante a integração, os testes detectaram e motivaram correções:

- Login malsucedido apagava cookie existente; a exclusão ficou restrita ao logout,
  evitando também uma resposta GET 401 antiga apagar um cookie novo.
- Leitura booleana divergente de AUTH_SECURE_COOKIE entre Python e Next.js.
- Guard reutilizável precisava do handler global para retornar 401 em qualquer rota.
- Teste de Voltar passou a observar a página restaurada antes de outra navegação.
- Timer passou a usar horário do servidor; teste de relógio adiantado aguarda a revalidação.
- Seletor de alertas foi distinguido do anunciador de rotas do Next.js.
- Uma execução simultânea de backend/navegador foi recusada pela proteção contra dados
  preexistentes. Após limpar somente a conta fictícia, as suítes passaram em sequência.
- O teste de indisponibilidade passou a esperar a hidratação e observar a resposta 503
  antes de conferir o aviso, evitando disparar foco antes da instalação do monitor.

## 6. Executar localmente

Na raiz, com Docker Desktop Linux aberto:

```powershell
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.cli.auth create
```

Confira o destino antes de migrar/provisionar. Informe username e senha apenas no
terminal interativo. Abra `http://localhost:3000/login`. Computador e celular podem
manter sessões distintas; acesso pela rede exige configuração explícita de host,
origem e portas. O Compose continua escutando no loopback por padrão.

Para reset administrativo com revogação de todas as sessões:

```powershell
docker compose exec backend python -m app.cli.auth reset-password
```

Configuração: AUTH_ORIGIN exata em ambos os aplicativos; AUTH_SECURE_COOKIE compatível;
BACKEND_INTERNAL_URL somente no servidor Next. Em produção: ENVIRONMENT=production,
origem HTTPS e cookie Secure. Não copiar senha para argumentos, código ou Git.

## 7. Reproduzir testes sem usar desenvolvimento

Use os recursos descartáveis da [Etapa 1](10-sprint-02-etapa-01.md). Reconstrua a imagem:

```powershell
docker build -f infra/backend.Dockerfile -t recephub-sprint02-backend:latest backend
```

A suíte backend usa TEST_DATABASE_URL explícita e TEST_DATABASE_ALLOW_RESET=1. Seu
banco deve estar vazio. O comando completo para o recurso usado nesta entrega é:

```powershell
docker run --rm --network recephub-sprint02-tests --mount "type=bind,source=$PWD\backend,target=/app,readonly" -e TEST_DATABASE_URL=postgresql+psycopg://recephub_test:ci-fictional-only@recephub-sprint02-test-db:5432/recephub_sprint02_test -e TEST_DATABASE_ALLOW_RESET=1 recephub-sprint02-backend:latest python -m pytest -p no:cacheprovider
```

Para navegador, depois da suíte backend, inicie uma API exclusivamente descartável:

```powershell
docker run -d --name recephub-sprint02-api-test --network recephub-sprint02-tests -p 127.0.0.1:3181:8000 --mount "type=bind,source=$PWD\backend,target=/app,readonly" -e POSTGRES_HOST=recephub-sprint02-test-db -e POSTGRES_DB=recephub_sprint02_test -e POSTGRES_USER=recephub_test -e POSTGRES_PASSWORD=ci-fictional-only -e AUTH_ORIGIN=http://127.0.0.1:3180 -e TEST_DATABASE_URL=postgresql+psycopg://recephub_test:ci-fictional-only@recephub-sprint02-test-db:5432/recephub_sprint02_test -e TEST_DATABASE_ALLOW_RESET=1 recephub-sprint02-backend:latest python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
cd frontend
npm ci
npx playwright install chromium
npm run build
npm run test:e2e
```

Se a API já existe, use o recurso existente em vez de repetir `docker run`. Ao terminar,
limpe somente a conta fictícia antes de repetir pytest:

```powershell
docker exec recephub-sprint02-api-test python -m tests.e2e_admin clean
```

O job browser da CI usa outro banco descartável, `recephub_browser_test`, isolado dos
outros jobs. As ferramentas de teste nunca escolhem o banco de desenvolvimento por fallback.

## 8. Warnings e limites

- Depreciação conhecida Starlette TestClient/httpx: mantida visível, sem filtros.
- npm audit continua reportando sete avisos moderados transitivos nas ferramentas
  TypeScript ESLint/minimatch. `npm audit fix` dentro das faixas compatíveis não os resolveu.
  Não foi forçada atualização major; os avisos permanecem registrados para manutenção.
- Playwright/Node emite aviso NO_COLOR/FORCE_COLOR, sem falha dos testes.
- Não há service worker, cache offline privado, push, deploy ou homologação de instalação
  em aparelho físico. Viewport mobile e dois contextos foram exercitados no Chromium.
- A conta administrativa real deve ser criada manualmente pela pessoa responsável.
- Não há recuperação por e-mail, cadastro público, JWT, Redis ou fluxo operacional além do estado vazio.

## 9. Preparação para a sprint seguinte

A próxima sprint pode partir da conta provisionada manualmente, guard reutilizável,
proxy restrito e fixtures fictícias. Unidades, colaboradoras e escalas continuam
dependendo das regras de negócio documentadas; esta sprint não resolve decisões de
jornada, cobertura, treinamento ou publicação. Revisar essas pendências antes de
implementar o Marco 2.
