# Sprint 03 — gestão operacional e identidade visual

Data: 13/11/2026. Situação: execução autorizada; implementação e validação locais aprovadas; publicação e CI em andamento.

## Autorização e base

O usuário aprovou a implementação integral do plano, com subagentes por etapa,
coordenação do avanço, commits sem Co-authored-by e publicação. Branches e PRs terão
destino `dev`; `main`, deploy e provisionamento de conta real ficam fora desta entrega.
O coordenador mantém as dependências funcionais, aplica integrações e executa testes.

Base: `df1dece`, CI aprovada em
[43332310079](https://github.com/MarcusSouza02/RecepHub/actions/runs/43332310079).
Essa evidência encerra a antiga pendência de Compose da Sprint 02; testes históricos
não substituem os testes desta sprint. `.env` e a mudança preexistente de `.env.example`
devem ser preservados. Dados e credenciais utilizados nos testes são fictícios.

## Decisões aprovadas

- Tabela normalizada `employee_work_patterns`, com sete dias explícitos por colaboradora.
- Estados `pending`, `working` e `non_working`; ausência de configuração não significa folga.
- Um período e um intervalo opcional por dia, sem atravessar meia-noite; sem regra presumida de sábado.
- Horários incompletos podem ser salvos; contradições conhecidas são rejeitadas.
- Subtotal em minutos apenas dos dias completos; total semanal somente com semana completa.
- Cálculo previsto aritmético, sem validar legislação, contrato ou horas efetivamente trabalhadas.
- Inativar unidade preserva vínculos e os sinaliza; novos vínculos exigem unidade ativa.
- Unidade habitual opcional; nomes homônimos permitidos; inativação/reativação por PATCH, sem DELETE.
- Autenticação da Sprint 02 preservada; todas as operações de negócio exigem sessão no backend.

JSONB foi comparado à tabela: simplifica a leitura do documento, mas concentra integridade
na aplicação. A tabela escolhida oferece unicidade por pessoa/dia, checks e consultas
relacionais adequadas à escala-base futura. Nenhuma tabela operacional futura é antecipada.

## Referência visual

URL: https://recephub.lovable.app/. A primeira leitura web e o host CUA falharam; o navegador
headless existente conseguiu acessar a referência pública com autorização de rede.
Dashboard, Unidades e Colaboradoras foram observados em 1440×1000 e 390×844.
Inventário e limites: [referência visual](13-sprint-03-referencia-visual.md).

Não foram importados código, autenticação, dados ou integrações do Lovable. A identidade
será reproduzida incrementalmente no Next.js existente. Elementos de escalas, cobertura,
ausências, IA e comunicações vistos no protótipo não serão habilitados nesta sprint.

## Quadro por etapa e commits

Estados: A fazer → Em andamento → Em revisão → Concluído. A coordenação foi delegada;
um aceite técnico depende de testes e revisão, não apenas da presença de arquivos.

| Card | Etapa | Entrega | Commit proposto | Estado |
|---|---|---|---|---|
| S03-01 | 0 | Encerramento documental da Sprint 02 | docs(sprint-02): record successful final CI validation | Registrado em 9a68bd9 |
| S03-02 | 0 | Referências visuais observadas e divergências | docs(sprint-03): document visual references and adaptation strategy | Registrado em 9a68bd9 |
| S03-03 | 0 | Plano, decisões e contratos | docs(sprint-03): define operational modules implementation plan | Registrado em 9a68bd9 |
| S03-04 | 1 | Unit e migração 0002 | feat(units): add unit persistence and migration | Implementado/testado localmente; CI pendente |
| S03-05 | 1 | API e consultas de unidades | feat(units): add authenticated management endpoints | Implementado/testado localmente; CI pendente |
| S03-06 | 1 | Persistência, API e segurança | test(units): cover management and access protection | Implementado/testado localmente; CI pendente |
| S03-07 | 2 | Tokens, shell e componentes compartilhados | feat(ui): align shared interface with approved visual reference | Implementado/testado localmente; CI pendente |
| S03-08 | 2 | Proxy restrito de unidades | feat(proxy): allow authenticated unit operations | Implementado/testado localmente; CI pendente |
| S03-09 | 2 | Interface de unidades | feat(units): add responsive management interface | Implementado/testado localmente; CI pendente |
| S03-10 | 2 | Fluxos de unidades no navegador | test(units): cover management browser flows | Implementado/testado localmente; CI pendente |
| S03-11 | 3 | Employee e migração 0003 | feat(employees): add persistence and optional home unit | Implementado/testado localmente; CI pendente |
| S03-12 | 3 | API, filtros e vínculos | feat(employees): add authenticated management endpoints | Implementado/testado localmente; CI pendente |
| S03-13 | 3 | Integridade e ciclo de vida | test(employees): cover relationships and lifecycle rules | Implementado/testado localmente; CI pendente |
| S03-14 | 4 | Proxy restrito de colaboradoras | feat(proxy): allow authenticated employee operations | Implementado/testado localmente; CI pendente |
| S03-15 | 4 | Interface de colaboradoras | feat(employees): add responsive management interface | Implementado/testado localmente; CI pendente |
| S03-16 | 4 | Equipe habitual por unidade | feat(units): display habitual employee assignments | Implementado/testado localmente; CI pendente |
| S03-17 | 4 | Fluxos de colaboradoras e vínculos | test(employees): cover management and unit assignments | Implementado/testado localmente; CI pendente |
| S03-18 | 5 | Padrões semanais e migração 0004 | feat(work-patterns): add normalized weekly persistence | Implementado/testado localmente; CI pendente |
| S03-19 | 5 | API e cálculo de minutos | feat(work-patterns): add weekly configuration and duration calculation | Implementado/testado localmente; CI pendente |
| S03-20 | 5 | Editor semanal com repetição explícita | feat(work-patterns): add responsive weekly editor | Implementado/testado localmente; CI pendente |
| S03-21 | 5 | Cálculos, incompletude e edição | test(work-patterns): cover weekly configuration and validation | Implementado/testado localmente; CI pendente |
| S03-22 | 6 | Resumo real protegido | feat(dashboard): add operational summary endpoint | Implementado/testado localmente; CI pendente |
| S03-23 | 6 | Indicadores e atalhos reais | feat(dashboard): display real operational indicators | Implementado/testado localmente; CI pendente |
| S03-24 | 6 | Regressão e homologação visual | test(sprint-03): cover operational end-to-end flows | Implementado/testado localmente; CI pendente |
| S03-25 | 6 | Relatório e encerramento | docs(sprint-03): document implementation and validation results | Relatório atualizado; CI e encerramento pendentes |

Branches, na ordem de integração: `feature/sprint-03-planning`,
`feature/sprint-03-units-backend`, `feature/sprint-03-units-ui`,
`feature/sprint-03-employees-backend`, `feature/sprint-03-employees-ui`,
`feature/sprint-03-work-patterns`, `feature/sprint-03-dashboard`.
Um PR por etapa, para `dev`. Os commits poderão agrupar cards dependentes, sem
quebrar uma entrega funcional. Preparação paralela de arquivos independentes é
permitida; registro e integração continuam sob controle exclusivo do coordenador.

## Contratos

Prefixo `/api/v1`; resposta de lista `{items,total,page,page_size}`. Paginação padrão
20, máximo 100; ordem por nome e UUID. Busca literal sem interpretar `%`/`_` como curingas.

| Recurso | Métodos e caminhos |
|---|---|
| Unidades | GET/POST /units; GET/PATCH /units/{id} |
| Colaboradoras | GET/POST /employees; GET/PATCH /employees/{id} |
| Equipe habitual | GET /units/{id}/employees |
| Semana habitual | GET/PUT /employees/{id}/work-patterns |
| Indicadores | GET /dashboard/summary |

Campos: Unit tem nome 120, cidade opcional 120, descrição opcional 500, active e
auditoria; Employee tem display_name 140, home_unit_id opcional, notes opcional 500,
active e auditoria. UUIDs e timestamps em UTC. Não há exclusão física por API.

Listagens aceitam q, status=active|inactive|all, page e page_size; colaboradoras também
home_unit_id ou without_home_unit, mutuamente exclusivos. PUT semanal exige exatamente
sete dias únicos (0=segunda, 6=domingo), grava atomicamente e retorna days com precisão
de minutos, duration_minutes/is_complete e subtotal_minutes/total_minutes/is_complete.

Códigos: 201 criação; 200 consulta/atualização; 401 sessão; 403 origem/CSRF; 404 inexistente;
409 vínculo impedido; 422 dados/filtros inválidos; 503 banco indisponível. Dados de erro
não incluem entradas sensíveis, SQL ou detalhes internos.

Proxy: caminhos e métodos explícitos, UUIDs e parâmetros conhecidos, sem destinos
livres. POST/PATCH/PUT exigem origem exata, CSRF, JSON e corpo até 4 KiB. Cookie,
Set-Cookie e política no-store continuam conforme Sprint 02.

## Aceite e testes

| Etapa | Evidência de aceite |
|---|---|
| 0 | Base/CI verificadas, referências observadas registradas, plano aprovado. |
| 1 | CRUD lógico real, busca/paginação e API protegida; migração validada em banco descartável. |
| 2 | Unidades funcionais, estados acessíveis e responsividade; referência aplicada sem dados fictícios como métricas reais. |
| 3 | Vínculo opcional, bloqueio de novos vínculos inativos, preservação de registros e filtros estáveis. |
| 4 | Colaboradoras funcionais, equipe por unidade e alertas de vínculo incompleto/inativo. |
| 5 | Sete dias explícitos, rascunhos preservados, validações, repetição e totais corretos. |
| 6 | Indicadores reais, autenticação preservada, CI aprovada e relatório com evidências. |

Testes: pytest/Ruff, migrações e checks PostgreSQL, lint/typecheck/build, Playwright
desktop/mobile, teclado, HTTP erros/CSRF/sessão, corpo e proxy, regressão de login/logout,
buscas e filtros combinados, vínculos, inativação, totais e rollback. Banco exclusivo
Sprint 03, fictício, sem downgrade/limpeza no desenvolvimento. Fixtures e testes que
pressupunham três tabelas deverão acompanhar o esquema e toda a cadeia de migrações.

Fora: escalas por data, férias/folgas, cobertura mínima, legislação, comunicações,
IA, deploy e mudanças de credenciais. Formulários e editor semanal não foram observados
na referência; sua adaptação usará os tokens e padrões compartilhados comprovados,
sem alegar reprodução de um comportamento que não foi inspecionado.

## Registro de execução

Arquivos e roteiro manual estão no [relatório técnico](14-sprint-03-relatorio-tecnico.md).
Backend: 153 testes aprovados em PostgreSQL 17 descartável, com um warning conhecido
do TestClient. Frontend: lint, TypeScript e build aprovados. Navegador: 26 casos aprovados
na primeira execução; dois seletores corrigidos e aprovados em nova execução desktop/mobile.
Revisão independente gpt-6-astra xhigh concluída sem bloqueadores após correções.
Commits locais: etapa 0 `9a68bd9`, etapa 1 `274d9a9`, etapa 2 `31c4021`, etapa 3
`782f69a`, etapa 4 `3a36b2b` e etapa 5 `3d9da95`. Ruff e formatação final aprovados
em 63 arquivos. Oito capturas locais desktop/mobile conferidas sem overflow ou erros
de página; indicadores reais verificados no DOM/API. Etapa 6, publicação e CI final em andamento;
não se declara a CI remota aprovada antes de observar seu resultado.
