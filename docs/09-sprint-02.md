# RecepHub — Sprint 02: quadro de cards

**Tema:** autenticação e acesso ao sistema  
**Data de organização:** 04/11/2026  
**Situação:** Etapa 1 implementada em 04/11/2026, em revisão; demais etapas aguardam autorização.

Este quadro transforma o planejamento técnico aprovado em entregas menores e verificáveis.
Cada card descreve o que será feito, as dependências e como comprovar a conclusão.
As sugestões de branch, commit e PR não representam operações Git já executadas.

## 1. Objetivo e decisões aprovadas

Entregar uma única conta administrativa, login/logout, sessões seguras no PostgreSQL,
proteção de acesso, interface de login e dashboard privado inicial.

| Decisão | Comportamento aprovado |
|---|---|
| Comunicação | Navegador → proxy Next.js por Route Handlers → FastAPI → PostgreSQL. |
| Autenticação | FastAPI é responsável por validar credenciais e sessões; o proxy não substitui essa validação. |
| Senha | Argon2id, sem senha padrão, cadastro público ou credenciais reais versionadas. |
| Sessão | Token opaco aleatório no cookie; somente seu SHA-256 no banco. |
| Validade | 12 horas desde o login ou 2 horas sem requisições autenticadas, o que ocorrer primeiro. |
| Dispositivos | Computador e celular podem manter sessões independentes. Logout encerra apenas a atual. |
| Cookies | HttpOnly, SameSite=Lax, Path=/, sem Domain; Secure e prefixo __Host- em produção HTTPS. |
| CSRF | Origem exata permitida e cabeçalho X-RecepHub-CSRF: 1 em operações de escrita, verificados no proxy e na API. |
| Tentativas | Cinco formulários válidos de login por janela de 15 minutos, inclusive sucessos; contador compartilhado e persistido no PostgreSQL. |
| Limite atingido | HTTP 429 com Retry-After; não encerra sessões abertas nem prolonga a janela por novas recusas. |
| Git | Branches pequenas a partir da dev atualizada; nenhuma mudança de branch, commit, push ou merge automática. |

Ficam fora: colaboradoras, unidades, escalas, férias/ausências, métricas operacionais, IA,
comunicações, JWT, Redis, OAuth e deploy. Redefinição de senha será administrativa, sem fluxo por e-mail.

## 2. Visão geral do quadro

Fluxo de cada card: **A fazer → Em andamento → Em revisão → Concluído**.
Use **Bloqueado** quando faltar uma dependência, acesso ou decisão, registrando o motivo.
Entrega implementada e testada vai para revisão; só a aprovação da pessoa responsável a conclui.

| Card | Etapa | Entrega | Dependências técnicas | Estado atual |
|---|---|---|---|---|
| [S02-00](#s02-00--consolidar-o-planejamento-técnico) | 0 | Planejamento e decisões | — | Concluído: planejamento aprovado |
| [S02-01](#s02-01--modelar-a-conta-administrativa) | 1 | Modelo User | S02-00 | Em revisão |
| [S02-02](#s02-02--modelar-as-sessões) | 1 | Modelo UserSession | S02-01 | Em revisão |
| [S02-03](#s02-03--criar-e-validar-a-primeira-migração) | 1 | Migração e testes de persistência | S02-01, S02-02 | Em revisão |
| [S02-04](#s02-04--implementar-hash-e-provisionamento-administrativo) | 2 | Argon2id e procedimento administrativo | S02-03 | A fazer |
| [S02-05](#s02-05--implementar-login-e-criação-da-sessão) | 2 | Login e cookie | S02-04 | A fazer |
| [S02-06](#s02-06--consultar-e-encerrar-a-sessão) | 2 | Consulta de sessão e logout | S02-05 | A fazer |
| [S02-07](#s02-07--consolidar-as-defesas-de-acesso-e-csrf) | 3 | Proteção, expiração e CSRF | S02-06 | A fazer |
| [S02-08](#s02-08--limitar-tentativas-de-login) | 3 | Limite persistente de tentativas | S02-07 | A fazer |
| [S02-09](#s02-09--consolidar-a-integração-e-os-checks-do-backend) | 3 | Integração e CI do backend | S02-07, S02-08 | A fazer |
| [S02-10](#s02-10--criar-o-proxy-de-mesma-origem) | 4 | Proxy Next.js | S02-09 | A fazer |
| [S02-11](#s02-11--criar-a-interface-de-login) | 4 | Formulário de login | S02-10 | A fazer |
| [S02-12](#s02-12--proteger-a-navegação-e-integrar-o-logout) | 4 | Guard de sessão e navegação | S02-11 | A fazer |
| [S02-13](#s02-13--montar-o-layout-privado-e-o-dashboard-vazio) | 5 | Área privada responsiva | S02-12 | A fazer |
| [S02-14](#s02-14--homologar-o-fluxo-completo) | 5 | Navegador, E2E e checks | S02-13 | A fazer |
| [S02-15](#s02-15--documentar-a-entrega-e-encerrar-a-sprint) | 5 | Relatório e revisão final | S02-14 | A fazer |

Dependência técnica satisfeita **não autoriza avanço**: ao terminar uma etapa, apresentar
resultados e diffs e aguardar autorização explícita para a próxima. Se for autorizado somente
um card, concluir apenas esse card e aguardar nova orientação.

## 3. Etapa 0 — Análise e planejamento

### S02-00 — Consolidar o planejamento técnico

**Estado:** concluído pelo planejamento aprovado pelo usuário.  
**Objetivo:** definir o desenho da autenticação antes de implementar.

**Entregas realizadas**

- [x] Conferir documentação, implementação, dependências e configuração existentes.
- [x] Identificar ausência de modelos/migrações, CORS apenas GET e comunicação direta atual.
- [x] Comparar acesso direto ao FastAPI e proxy pelo Next.js.
- [x] Definir conta, sessões, cookies, contratos, CSRF e tentativas de login.
- [x] Definir etapas, dependências, testes e fluxo de revisão.
- [x] Obter aprovação do planejamento e organizar este quadro.

**Evidências:** na análise foram aprovados dez testes unitários, Ruff, ESLint e TypeScript.
Integração PostgreSQL e CI remota não foram reexecutadas nessa análise; o warning conhecido
de httpx/TestClient permaneceu registrado.

**Limite:** aprovação do planejamento e deste quadro não significa implementação dos cards seguintes.

## 4. Etapa 1 — Persistência e migrações

**Resultado esperado da etapa:** esquema de autenticação real, testado em banco descartável.
Sem endpoints, hash funcional ou interface nesta etapa.

### S02-01 — Modelar a conta administrativa

**Estado:** em revisão (04/11/2026). **Depende de:** S02-00 e autorização da Etapa 1.

**Objetivo:** representar a única conta de acesso, preservando o modelo de negócio proposto.

**Entregas**

- [x] Criar User com UUID, username, password_hash, active e created_at.
- [x] Acrescentar login_window_started_at e login_attempt_count para o controle posterior de tentativas.
- [x] Definir username canônico: minúsculas, sem espaços externos, 3–80 caracteres ASCII entre letras, números, ponto, hífen e sublinhado.
- [x] Declarar unicidade do username e índice único sobre constante true para no máximo uma conta, inclusive inativa.
- [x] Nomear constraints conforme a convenção existente e usar timestamps com fuso/UTC.

**Áreas previstas:** `backend/app/models/user.py`, agregador de modelos e modelagem documental.

**Aceite e verificação**

- [x] Metadados descrevem campos, defaults e constraints aprovados.
- [x] A validação PostgreSQL no S02-03 comprova que uma segunda conta e username inválido não são aceitos.
- [x] Nenhuma senha, conta efetiva ou tabela de outro módulo é criada por este card.

### S02-02 — Modelar as sessões

**Estado:** em revisão (04/11/2026). **Depende de:** S02-01.

**Objetivo:** permitir expiração e revogação por dispositivo sem guardar o token original.

**Entregas**

- [x] Criar UserSession com id, user_id, token_hash, created_at, expires_at, last_seen_at e revoked_at.
- [x] Relacionar com User por FK com exclusão em cascata.
- [x] Definir token_hash CHAR(64) obrigatório e único, índice em user_id e constraints temporais nomeadas.
- [x] Permitir várias sessões para a mesma conta.
- [x] Registrar os modelos para descoberta pelo Alembic.

**Áreas previstas:** `backend/app/models/user_session.py`, agregador de modelos e ambiente Alembic.

**Aceite e verificação**

- [x] O esquema não contém coluna de token de sessão em texto original.
- [x] O S02-03 comprova FK, hash único, múltiplas sessões e coerência dos horários.
- [x] Não há geração de tokens ou endpoints neste card.

### S02-03 — Criar e validar a primeira migração

**Estado:** em revisão (04/11/2026). **Depende de:** S02-01 e S02-02.

**Objetivo:** tornar o esquema reproduzível e comprovar suas garantias no PostgreSQL.

**Entregas**

- [x] Criar e revisar a primeira revisão Alembic, com down_revision=None, somente para users e user_sessions.
- [x] Acrescentar fixtures e testes de persistência em banco descartável específico da Sprint 02.
- [x] Testar constraints dos dois modelos e exclusão em cascata.
- [x] Executar upgrade, downgrade e novo upgrade no banco descartável.
- [x] Executar alembic check e regressão de saúde.
- [x] Ajustar a ordem da CI para aplicar migrações antes dos testes que dependem do esquema.
- [x] Atualizar a modelagem e registrar resultados da etapa.

**Áreas previstas:** `backend/alembic/`, `backend/tests/test_auth_models.py`, fixtures,
`.github/workflows/ci.yml` e `docs/04-modelagem-banco.md`.

**Aceite e verificação**

- [x] Upgrade/downgrade/upgrade passam; alembic check não encontra diferenças pendentes.
- [x] Testes de persistência e regressão passam com dados fictícios.
- [x] Não há downgrade, limpeza ou troca de credenciais no banco de desenvolvimento.
- [x] O antigo recephub-test-db não é reutilizado ou removido automaticamente.

**Checkpoint:** apresentar modelos, SQL/migração, diffs e resultados; aguardar revisão e
autorização da Etapa 2. A aplicação da migração ao banco de desenvolvimento deve ser explicitada
no plano de execução da etapa, sem confundir com os ciclos destrutivos do banco descartável.

### Evidências da entrega da Etapa 1

65 testes passaram em PostgreSQL 17 descartável, incluindo upgrade/downgrade/upgrade
e `alembic check`; Ruff e formatação passaram. Banco de desenvolvimento não migrado.
Arquivos, comandos, diffs e limitações: [relatório da Etapa 1](10-sprint-02-etapa-01.md).
A aprovação dos três cards e o início da Etapa 2 aguardam revisão e autorização explícita.

## 5. Etapa 2 — Autenticação backend

**Resultado esperado da etapa:** credenciais e sessões funcionando por API, sem interface visual.
Os endpoints já devem nascer com as defesas mínimas; a Etapa 3 aprofunda proteção e testes.

### S02-04 — Implementar hash e provisionamento administrativo

**Estado:** a fazer. **Depende de:** S02-03 e autorização da Etapa 2.

**Objetivo:** cadastrar a conta inicial e administrar a senha sem expô-la em arquivos ou comandos.

**Entregas**

- [ ] Adicionar argon2-cffi, justificar a dependência e atualizar o lock.
- [ ] Implementar hash, verificação e rehash com Argon2id: inicialmente 64 MiB, três iterações, paralelismo 1, salt 16 bytes e hash 32 bytes.
- [ ] Medir o custo do hash no container e registrar o resultado.
- [ ] Criar comando administrativo com getpass e confirmação, sem senha em argumento.
- [ ] Exigir senha de 15–128 caracteres, sem aparar espaços ou impor composição artificial.
- [ ] Recusar criação de segunda conta; permitir redefinição da existente com revogação de suas sessões.

**Áreas previstas:** `backend/app/core/security.py`, `backend/app/cli/auth.py`, serviço/repositório,
manifests Python e testes de senha/provisionamento.

**Aceite e verificação**

- [ ] Hash corresponde a Argon2id; senha correta verifica e incorreta falha.
- [ ] Testes cobrem duplicação, entradas inválidas e redefinição com revogação.
- [ ] Senha não aparece em saída, logs ou arquivos versionados.
- [ ] Conta efetiva é provisionada manualmente pela pessoa responsável, sem conta/senha padrão automática.

### S02-05 — Implementar login e criação da sessão

**Estado:** a fazer. **Depende de:** S02-04.

**Objetivo:** autenticar a conta e criar uma sessão independente para o navegador.

**Entregas**

- [ ] Implementar POST /api/v1/auth/login com JSON username/password.
- [ ] Validar origem permitida, X-RecepHub-CSRF: 1 e application/json desde a primeira versão.
- [ ] Limitar corpo a 4 KiB e sanitizar erros de validação, sem ecoar a senha.
- [ ] Retornar o mesmo erro para senha incorreta, usuário inexistente ou inativo.
- [ ] Gerar token aleatório de 32 bytes, persistir somente SHA-256 e emitir cookie conforme ambiente.
- [ ] Retornar user, expires_at e idle_expires_at, sem token ou hash.
- [ ] Substituir/revogar sessão anterior do mesmo navegador sem revogar outros dispositivos.
- [ ] Implementar transação de criação e tratamento de falha de banco sem confirmação indevida de sucesso.

**Áreas previstas:** schemas/auth, services/auth, repositories/auth, api/v1/auth, settings,
router, tratamento de erros e testes do backend.

**Aceite e verificação**

- [ ] Sucesso retorna 200 e cookie; credenciais inválidas retornam 401 uniforme.
- [ ] Banco guarda somente hash e timestamps corretos; cookie recebido do cliente não é reaproveitado como novo token.
- [ ] Testes conferem atributos do cookie, validação e ausência de credenciais em respostas/logs.
- [ ] Configuração de produção exige HTTPS/cookie Secure; valores reais do .env não são alterados automaticamente.

### S02-06 — Consultar e encerrar a sessão

**Estado:** a fazer. **Depende de:** S02-05.

**Objetivo:** reconhecer a usuária autenticada e permitir logout com revogação efetiva.

**Entregas**

- [ ] Implementar GET /api/v1/auth/session com o contrato de sessão aprovado.
- [ ] Verificar token, usuário ativo, revogação e limites absoluto/inativo no servidor.
- [ ] Atualizar last_seen_at sem ultrapassar a expiração absoluta.
- [ ] Implementar POST /api/v1/auth/logout com origem/cabeçalho CSRF exigidos.
- [ ] Revogar sessão atual e excluir cookie; logout repetido deve ser idempotente após a validação CSRF.
- [ ] Retornar 503 se a revogação falhar no banco, sem afirmar que logout foi concluído.
- [ ] Usar Cache-Control: no-store nas respostas de autenticação.

**Áreas previstas:** endpoints/serviço/repositório de autenticação, dependências da API e testes.

**Aceite e verificação**

- [ ] Consulta válida retorna 200; ausente, expirada ou revogada retorna 401.
- [ ] Logout retorna 204 após revogação; token anterior deixa de autenticar.
- [ ] Logout de uma sessão não revoga a de outro dispositivo.
- [ ] Testes não usam dados reais e verificam falha de banco e repetição do logout.

**Checkpoint:** apresentar fluxo HTTP, cookies, transações, comandos administrativos e testes;
aguardar revisão e autorização da Etapa 3. Backend funcional ainda não significa publicação homologada.

## 6. Etapa 3 — Segurança e testes

**Resultado esperado da etapa:** backend protegido e validado em cenários adversos, preservando
os endpoints públicos de infraestrutura.

### S02-07 — Consolidar as defesas de acesso e CSRF

**Estado:** a fazer. **Depende de:** S02-06 e autorização da Etapa 3.

**Objetivo:** verificar que sessão inválida e requisições forjadas não liberam acesso nem alteram estado.

**Entregas**

- [ ] Consolidar dependência reutilizável de autenticação para endpoints privados.
- [ ] Testar origem ausente, null, não autorizada e cabeçalho CSRF ausente/incorreto em login/logout.
- [ ] Confirmar bloqueio de formatos de conteúdo inadequados e sanitização de erros.
- [ ] Testar expiração de 12 horas e inatividade de 2 horas com relógio controlado.
- [ ] Testar token adulterado, usuário inativo e revogação concorrente com atualização de atividade.
- [ ] Preparar CORS para a arquitetura de mesma origem, sem credenciais para origens externas.

**Áreas previstas:** segurança, dependências, settings, serviço de autenticação e testes adversos.

**Aceite e verificação**

- [ ] API nega acesso independentemente de qualquer proteção visual do frontend.
- [ ] Requisição concorrente não reativa sessão revogada.
- [ ] CSRF é verificado no backend, não somente por SameSite ou pela futura interface.
- [ ] Nenhum GET realiza operação de login/logout; saúde e prontidão permanecem públicas.

### S02-08 — Limitar tentativas de login

**Estado:** a fazer. **Depende de:** S02-07.

**Objetivo:** limitar novas autenticações de forma persistente, sem Redis ou confiança no IP do proxy.

**Entregas**

- [ ] Usar os campos de janela/contador de User criados na Etapa 1.
- [ ] Reservar tentativa em transação curta com bloqueio da linha antes de verificar a senha.
- [ ] Contar cinco formulários válidos por 15 minutos, incluindo sucessos e usuários informados incorretamente.
- [ ] Retornar 429 e Retry-After ao atingir o limite, sem prolongar a janela por recusas posteriores.
- [ ] Reiniciar a janela quando o período terminar, sem zerá-la em um login bem-sucedido.
- [ ] Manter sessões já abertas operantes e o contador efetivo após reinicialização da API.

**Áreas previstas:** serviço/repositório de autenticação, settings e testes de limite/concorrência.

**Aceite e verificação**

- [ ] Cinco tentativas são contabilizadas; a sexta é recusada até terminar a janela.
- [ ] Concorrência não ultrapassa o limite; não há dependência de estado apenas em memória.
- [ ] Testes cobrem Retry-After, término da janela, sucessos contabilizados e ausência de impacto sobre sessões abertas.

### S02-09 — Consolidar a integração e os checks do backend

**Estado:** a fazer. **Depende de:** S02-07 e S02-08.

**Objetivo:** reunir evidência reproduzível de que persistência, autenticação e segurança funcionam juntas.

**Entregas**

- [ ] Isolar sessões, contadores e contas fictícias por teste.
- [ ] Executar integração contra PostgreSQL descartável da Sprint 02.
- [ ] Conferir que fixtures nunca apontam ciclos destrutivos para o banco de desenvolvimento.
- [ ] Consolidar testes de login, revogação, expiração, CSRF, tentativas e indisponibilidade.
- [ ] Ajustar workflow para migrações, testes, Ruff e regressão de infraestrutura.
- [ ] Documentar resultados, falhas e warnings, sem filtros para ocultá-los.

**Áreas previstas:** `backend/tests/`, workflow, documentação de execução e evidências.

**Aceite e verificação**

- [ ] Bateria backend passa sem depender de sessão ou credencial real.
- [ ] Health, prontidão e documentação FastAPI mantêm os contratos esperados.
- [ ] Ruff passa; warning conhecido do TestClient é reportado, não ignorado.
- [ ] CI configurada e execução remota observada são registradas como situações distintas.

**Checkpoint:** apresentar matriz de testes, resultados e diffs; aguardar autorização da Etapa 4.
Os testes de cada card anterior continuam obrigatórios: este card consolida, não adia testes.

## 7. Etapa 4 — Frontend e login

**Resultado esperado da etapa:** acesso autenticado por mesma origem, formulário de login e
dashboard mínimo protegido, ainda sem o layout privado completo.

### S02-10 — Criar o proxy de mesma origem

**Estado:** a fazer. **Depende de:** S02-09 e autorização da Etapa 4.

**Objetivo:** fazer o navegador conversar somente com o Next.js para autenticação e prontidão.

**Entregas**

- [ ] Criar Route Handler para lista restrita de caminhos/métodos de autenticação e prontidão.
- [ ] Usar BACKEND_INTERNAL_URL exclusivo do servidor, com destino fixo e sem URL fornecida pelo cliente.
- [ ] Encaminhar somente cookie de sessão e cabeçalhos necessários, preservando Set-Cookie e sua exclusão.
- [ ] Validar origem/cabeçalho CSRF antes de encaminhar escritas; não completar requisições inválidas automaticamente.
- [ ] Tratar timeout/indisponibilidade sem expor detalhes nem converter erro técnico em 401.
- [ ] Migrar o indicador de saúde existente para URL relativa e finalizar ajustes de CORS/configuração.

**Áreas previstas:** `frontend/src/app/api/v1/[...path]/route.ts`, serviços HTTP,
Compose, exemplo de ambiente e testes do proxy.

**Aceite e verificação**

- [ ] Navegador usa a mesma origem para login, sessão, logout e prontidão.
- [ ] Destinos não autorizados não são encaminhados; cookies não vazam entre clientes.
- [ ] Testes conferem criação/exclusão do cookie e falha upstream.
- [ ] Health checks Docker continuam funcionando e tokens não aparecem em logs.

### S02-11 — Criar a interface de login

**Estado:** a fazer. **Depende de:** S02-10.

**Objetivo:** permitir acesso compreensível e responsivo, distinguindo credencial incorreta de falha técnica.

**Entregas**

- [ ] Criar /login com username, senha e envio pelo proxy.
- [ ] Usar Tailwind/componentes básicos da estrutura shadcn existente, sem biblioteca adicional de formulários.
- [ ] Tratar loading, erro de credenciais, validação, limite de tentativas e indisponibilidade.
- [ ] Evitar envio duplicado durante processamento e oferecer feedback acessível.
- [ ] Adicionar @playwright/test como dependência de desenvolvimento com versão exata no lock e preparar E2E.
- [ ] Não armazenar tokens em localStorage, sessionStorage, props ou JSON.

**Áreas previstas:** página /login, feature e serviço de autenticação, componentes de formulário,
manifest/lock npm e configuração/testes Playwright.

**Aceite e verificação**

- [ ] Login válido leva ao dashboard; erro não revela existência de conta nem repete a senha.
- [ ] 429 e 503 têm mensagens apropriadas e não são exibidos como senha incorreta.
- [ ] Lint, TypeScript e build passam; primeiro teste do formulário é executado em navegador.

### S02-12 — Proteger a navegação e integrar o logout

**Estado:** a fazer. **Depende de:** S02-11.

**Objetivo:** impedir renderização indevida de conteúdo privado e descartar estado anterior após logout.

**Entregas**

- [ ] Criar guard de servidor que consulta a sessão no FastAPI antes de renderizar a página privada.
- [ ] Implementar /dashboard mínimo protegido e encaminhamento de / para login/dashboard conforme sessão.
- [ ] Não confiar apenas no layout, middleware ou presença do cookie.
- [ ] Integrar logout, respeitando falha de revogação sem anunciar sucesso indevido.
- [ ] Fazer navegação completa com substituição de histórico nas fronteiras login/logout e não compartilhar conteúdo privado por cache.
- [ ] Tratar 401 como sessão inválida e 503 como indisponibilidade, sem confundi-los.

**Áreas previstas:** guard de servidor, página inicial, página privada mínima,
serviço/feature de autenticação e testes de navegação.

**Aceite e verificação**

- [ ] Acesso direto anônimo e cookie falso não liberam conteúdo privado.
- [ ] Logout revoga antes de levar à tela de login; token anterior não funciona.
- [ ] Reabrir navegador dentro da validade mantém sessão; expiração exige novo login.
- [ ] Testes verificam que Voltar após logout não restaura dashboard utilizável.

**Checkpoint:** apresentar proxy, cookies no navegador, fluxo de login/logout e diffs;
aguardar revisão e autorização da Etapa 5.

## 8. Etapa 5 — Layout privado e homologação

**Resultado esperado da etapa:** área privada inicial utilizável e sprint homologada, com
resultados de testes e documentação de encerramento.

### S02-13 — Montar o layout privado e o dashboard vazio

**Estado:** a fazer. **Depende de:** S02-12 e autorização da Etapa 5.

**Objetivo:** oferecer uma base administrativa clara sem antecipar módulos operacionais.

**Entregas**

- [ ] Criar layout privado com sidebar desktop e navegação superior mobile.
- [ ] Disponibilizar Dashboard e Sair, com identidade da conta autenticada.
- [ ] Apresentar estado vazio explícito, sem números fictícios como métricas reais.
- [ ] Tratar expiração da sessão durante uso e preservar guard de servidor.
- [ ] Preservar manifest, ícones e compatibilidade com a estrutura PWA inicial.

**Áreas previstas:** layout privado, componentes de navegação e dashboard.

**Aceite e verificação**

- [ ] Navegação funciona em desktop/mobile e por teclado, com foco e rótulos apropriados.
- [ ] Não há telas funcionais ou links operacionais de colaboradoras, unidades, escalas ou ausências.
- [ ] Nenhuma métrica é apresentada como se viesse de um módulo ainda inexistente.

### S02-14 — Homologar o fluxo completo

**Estado:** a fazer. **Depende de:** S02-13.

**Objetivo:** provar o funcionamento do conjunto, além dos testes unitários e do build.

**Entregas**

- [ ] Executar login, consulta, navegação e logout em navegador real com dados fictícios.
- [ ] Testar contextos independentes para computador e celular e logout de apenas um dispositivo.
- [ ] Verificar erro de credenciais, expiração, 429, indisponibilidade e acesso anônimo direto.
- [ ] Verificar histórico após logout, teclado/foco, mobile e desktop.
- [ ] Conferir manifest/ícones e ausência de cache offline de respostas privadas.
- [ ] Executar regressão backend, integração, Ruff, ESLint, TypeScript, build e E2E.
- [ ] Observar resultados dos checks no GitHub após publicação autorizada, sem push automático.

**Áreas previstas:** testes E2E, testes backend, workflow e evidências de homologação.

**Aceite e verificação**

- [ ] Evidências distinguem testes locais, navegador e CI remota efetivamente executados.
- [ ] Fluxo de dois dispositivos funciona com sessões independentes.
- [ ] Falha ou indisponibilidade de ferramenta fica registrada como pendência, não como aprovação.
- [ ] Sem navegador validado ou checks remotos observados, a homologação final não é declarada concluída.

### S02-15 — Documentar a entrega e encerrar a sprint

**Estado:** a fazer. **Depende de:** S02-14.

**Objetivo:** deixar a entrega compreensível, reproduzível e pronta para planejar a sprint seguinte.

**Entregas**

- [ ] Atualizar README com migração, provisionamento, execução, login/logout e verificação manual.
- [ ] Atualizar arquitetura, modelagem e roadmap conforme o que foi implementado/aprovado.
- [ ] Consolidar relatório técnico da Sprint 02, com arquivos, conceitos, diffs relevantes e testes reais.
- [ ] Registrar dependências novas, warnings, limitações e pendências futuras.
- [ ] Conferir critérios de aceite e apresentar sugestões de commit/PR para revisão.
- [ ] Atualizar estados dos cards apenas conforme implementação e aprovação efetivas.

**Áreas previstas:** README, documentos de arquitetura/modelagem/roadmap e registro da Sprint 02.

**Aceite e verificação**

- [ ] Documentação permite reproduzir ambiente, migração e testes sem credenciais reais versionadas.
- [ ] Há evidência dos onze critérios de aceite resumidos na seção 10.
- [ ] Usuário revisa a entrega e as pendências antes de considerar a sprint encerrada.

**Checkpoint:** apresentar relatório e revisão final. Encerrar a sprint não autoriza iniciar outra,
publicar em produção ou fazer merge para main.

## 9. Git e revisão por etapa

Os cards são unidades de acompanhamento. Uma etapa pode reunir vários cards em um PR;
não é obrigatório criar um commit por card. Estas mensagens continuam sendo sugestões:

| Etapa / cards | Branch sugerida | Commit sugerido | PR |
|---|---|---|---|
| 1 / S02-01–03 | feature/sprint-02-auth-persistence | feat(auth): add user and session persistence | Para dev |
| 2 / S02-04–06 | feature/sprint-02-auth-backend | feat(auth): implement account provisioning and sessions | Para dev |
| 3 / S02-07–09 | feature/sprint-02-auth-security | feat(auth): enforce csrf protection and login throttling | Para dev |
| 4 / S02-10–12 | feature/sprint-02-login | feat(auth): add same-origin proxy and login interface | Para dev |
| 5 / S02-13–15 | feature/sprint-02-private-layout | feat(ui): add private dashboard and auth verification | Para dev |

Antes de criar cada branch, conferir a dev atualizada e as alterações locais com autorização
para as operações necessárias. A etapa seguinte partirá da dev que recebeu a etapa anterior.
Não trocar branch, fazer stash, commit, push ou merge automaticamente. Preservar a alteração
preexistente em .env.example e não modificar credenciais reais por causa destes cards.

### Evidência obrigatória ao entregar cada etapa

1. Objetivo e cards atendidos.
2. Arquivos criados/modificados e diffs relevantes.
3. Conceitos técnicos e fluxo de funcionamento.
4. Como executar e testar manualmente.
5. Testes automatizados e resultados observados.
6. Problemas, warnings e limitações.
7. Sugestões de commit e PR.
8. Dependências e preparação da etapa seguinte.
9. Pausa para revisão e nova autorização.

## 10. Conferência final dos critérios de aceite

| Critério da sprint | Cards que entregam a evidência |
|---|---|
| 1. Primeira migração real aplicada e testada | S02-01, S02-02, S02-03 |
| 2. Conta inicial provisionada administrativamente | S02-04 |
| 3. Senha armazenada com hash seguro | S02-04, S02-05 |
| 4. Login e logout funcionais | S02-05, S02-06, S02-11, S02-12, S02-14 |
| 5. Sessões com expiração e revogação | S02-02, S02-06, S02-07, S02-14 |
| 6. Endpoints privados protegidos | S02-06, S02-07, S02-12 |
| 7. Defesa contra abuso e CSRF | S02-05, S02-06, S02-07, S02-08, S02-10 |
| 8. Login responsivo | S02-11, S02-14 |
| 9. Dashboard inicial privado | S02-12, S02-13, S02-14 |
| 10. Testes locais e GitHub Actions aprovados | S02-03, S02-09, S02-14 |
| 11. Documentação atualizada | S02-15 e registros incrementais das etapas |

## 11. Referências e manutenção do quadro

- [Requisitos](02-requisitos.md): especialmente RF-01 e requisitos não funcionais de segurança/qualidade.
- [Modelagem](04-modelagem-banco.md): base de users, a ampliar com sessões na Etapa 1.
- [Arquitetura](05-arquitetura.md): conta única, hash, cookies e backend responsável pela validação.
- [Roadmap](06-roadmap.md): esta sprint completa a parte de autenticação do Marco 1.
- [Relatório da Sprint 01](08-sprint-01-relatorio-tecnico.md): ponto de partida, verificações históricas e pendências.
- [README](../README.md): execução do ambiente existente.

Ao iniciar um card autorizado, registrar data e estado; ao entregá-lo, acrescentar arquivos,
comandos/resultados e limitações; após aprovação, marcar conclusão. Ajustes que alterem escopo
ou decisões aprovadas devem ser apresentados para revisão antes da implementação.
