# Sprint 03 — relatório técnico de execução

**Atualizado em:** 13/11/2026. **Estado:** implementação, testes locais e revisão concluídos; publicação e CI final em andamento.

Este documento descreve arquivos, decisões e resultados efetivamente reportados pelo
coordenador. A validação local está concluída; a CI desta entrega ainda deve ser observada.
A Sprint 02 possui CI aprovada em `df1dece`,
[execução 43332310079](https://github.com/MarcusSouza02/RecepHub/actions/runs/43332310079);
essa evidência histórica não valida o novo código da Sprint 03.

## 1. Escopo e coordenação

O usuário delegou execução das etapas, subagentes, revisão independente, commits sem
coautor e publicação para `dev`. Não foram autorizados deploy, merge para `main`,
criação de conta real ou troca de credenciais. `.env` e a alteração preexistente de
`.env.example` devem permanecer preservados e fora dos commits desta entrega.

As etapas são planejamento, backend de unidades, interface de unidades, backend de
colaboradoras, interface de colaboradoras, horários habituais e dashboard/homologação.
O [quadro de cards](12-sprint-03.md) mantém dependências e critérios de aceite.

## 2. Comportamento implementado e decisões

Unidades e colaboradoras têm cadastro, consulta, busca, paginação e alteração de status.
Não existe DELETE público. A unidade habitual é opcional; homônimos são permitidos.
Inativar unidade preserva os vínculos já cadastrados e a interface deve sinalizá-los.
Novos vínculos exigem unidade ativa; manter um vínculo existente com unidade inativa
ou desvincular a colaboradora continua permitido.

Cada colaboradora possui sete registros semanais explícitos, começando pendentes.
Há um turno e um intervalo opcional por dia, sem virada de meia-noite ou presunção de
sábado. Rascunhos incompletos podem ser salvos, mas horários contraditórios são rejeitados.
Dias completos compõem o subtotal; total semanal permanece nulo até todos os dias
estarem definidos. Os minutos são previstos por aritmética, sem interpretação trabalhista.

O desenho continua simples: navegador → proxy Next.js → rotas FastAPI → serviços e
repositórios → PostgreSQL. A autenticação da Sprint 02 continua sendo a autoridade:
sessão exigida no backend, escrita com origem/CSRF/JSON, cookie HttpOnly e respostas
sem cache. O proxy autoriza apenas combinações explícitas de caminhos e métodos.

## 3. Inventário do backend

Os caminhos desta tabela são relativos a `backend/`.

| Arquivos | Alteração e finalidade |
|---|---|
| `app/models/unit.py` | Unit com UUID, nome, cidade e descrição opcionais, status e auditoria UTC; validação de nome não vazio. |
| `app/models/employee.py` | Employee com nome, observações, status e FK opcional para unidade, preservando integridade relacional. |
| `app/models/employee_work_pattern.py` | Dia habitual normalizado, unicidade pessoa/dia e checks de estado, limites e horários. |
| `app/models/__init__.py` | Registro dos novos modelos para metadados, fixtures e descoberta Alembic. |
| `alembic/versions/0002_units.py` | Criação de unidades, constraints e índices; depende da fundação de autenticação. |
| `alembic/versions/0003_employees.py` | Criação de colaboradoras e FK opcional de unidade. |
| `alembic/versions/0004_employee_work_patterns.py` | Tabela semanal e preenchimento de sete dias pendentes para colaboradoras anteriores. |
| `app/schemas/units.py` | Contratos de criação, patch, consulta e retorno; limites, normalização e paginação. |
| `app/schemas/employees.py` | Contratos de colaboradoras, filtros por vínculo e representação pública da unidade habitual. |
| `app/schemas/work_patterns.py` | Sete dias únicos, estados e horários; validações cruzadas, completude e cálculo de minutos. |
| `app/repositories/units.py` | Consulta individual e listagem com busca literal, contagem e ordenação estável. |
| `app/repositories/employees.py` | Filtros combinados por status/unidade/sem unidade e carregamento dos vínculos. |
| `app/repositories/work_patterns.py` | Leitura ordenada dos dias habituais por colaboradora. |
| `app/services/units.py` | Casos de uso de unidades, persistência e inativação lógica. |
| `app/services/employees.py` | Criação/edição, verificação de unidade ativa sob bloqueio e inicialização dos dias pendentes na mesma transação. |
| `app/services/work_patterns.py` | Consulta e substituição atômica da semana, bloqueio da colaboradora e representação dos totais. |
| `app/api/v1/units.py` | GET/POST de coleção e GET/PATCH individual, sessão obrigatória e defesas de escrita. |
| `app/api/v1/employees.py` | Rotas de colaboradoras e consulta de equipe habitual da unidade. |
| `app/api/v1/work_patterns.py` | GET/PUT da semana, sem atualização parcial silenciosa. |
| `app/api/v1/router.py` | Integração dos módulos na API versionada existente. |
| `app/api/v1/dashboard.py` | Três contagens reais em uma única instrução SQL, no mesmo snapshot: unidades ativas, colaboradoras ativas e ativas sem unidade. |
| `tests/test_units.py` | Regras de unidade, API e persistência. |
| `tests/test_employees.py` | Regras de vínculo, filtros e inativação. |
| `tests/test_work_patterns.py` | Estados, validações, minutos e persistência semanal. |
| `tests/conftest.py`, `tests/test_auth_migrations.py` | Infraestrutura de testes adaptada ao esquema ampliado, validando cadeia de migrações em banco descartável. |
| `tests/test_dashboard.py` | Contagens reais e proteção do resumo operacional. |
| `tests/e2e_admin.py` | Preparação e reset de dados estritamente fictícios em banco de navegador descartável, separado do desenvolvimento. |

## 4. Inventário do frontend

Os caminhos desta tabela são relativos a `frontend/`.

| Arquivos | Alteração e finalidade |
|---|---|
| `src/app/globals.css` | Tokens de cor, tipografia, superfície, bordas e foco conforme referência observada. |
| `src/components/ui/operations.tsx` | Campos, botões, alertas, status, paginação e confirmação compartilhados. |
| `src/features/dashboard/private-shell.tsx`, `navigation.tsx` | Shell privado e navegação responsiva, preservando monitor de sessão e logout. |
| `src/services/operations.ts` | Cliente HTTP de operações e erros públicos; requisições pela mesma origem. |
| `src/app/api/v1/[...path]/route.ts` | Ampliação restrita do proxy; métodos/caminhos/parâmetros explícitos e defesas de escrita. |
| `src/app/units/page.tsx`, `new/page.tsx`, `[id]/page.tsx`, `[id]/edit/page.tsx` | Entradas de servidor protegidas para listagem, criação, detalhes e edição de unidades. |
| `src/features/units/units-client.tsx` | Fluxos de unidade, busca, formulários, carregamento, erros e confirmação de status. |
| `src/features/units/unit-team.tsx` | Equipe habitual real da unidade, sem confundir vínculo com presença no dia. |
| `src/app/employees/page.tsx`, `new/page.tsx`, `[id]/page.tsx`, `[id]/edit/page.tsx` | Páginas privadas de colaboradoras. |
| `src/features/employees/employees-client.tsx`, `types.ts` | Lista/filtros, formulário, detalhes e tipos; unidade opcional e sinalização de vínculos inativos. |
| `src/features/work-patterns/weekly-editor.tsx`, `types.ts` | Editor semanal, estados explícitos, cópia deliberada entre dias e feedback de totais/incompletude. |
| `src/features/dashboard/summary.tsx`, `src/app/dashboard/page.tsx` | Indicadores reais, atalhos, carregamento, erro e nova tentativa; sem métricas fictícias de presença diária. |
| `public/fonts/manrope-variable.ttf`, `sora-variable.ttf`, arquivos OFL | Fontes locais e licenças, sem carregamento remoto em tempo de execução. Atribuição em `THIRD_PARTY_NOTICES.md`. |
| `tests/e2e/operations.spec.ts`, `tests/e2e/auth.spec.ts` | Fluxos operacionais e regressão da autenticação em navegador. |

A [referência visual](13-sprint-03-referencia-visual.md) distingue páginas efetivamente
observadas de formulários/editor não inspecionados; não há alegação de fidelidade visual
verificada para telas que não foram abertas no protótipo.

## 5. Contratos e garantias

Sob `/api/v1`: `GET/POST /units`, `GET/PATCH /units/{id}`,
`GET/POST /employees`, `GET/PATCH /employees/{id}`,
`GET /units/{id}/employees`, `GET/PUT /employees/{id}/work-patterns`.
O resumo é `GET /dashboard/summary`, com `active_units`, `active_employees` e
`active_employees_without_home_unit`.

Listas retornam `items`, `total`, `page`, `page_size`; padrão 20, máximo 100.
Busca é literal, status aceita active/inactive/all, e ordem nome/UUID evita paginação
instável em homônimos. Colaboradoras aceitam unidade ou filtro sem unidade.
Criação retorna 201, consulta/atualização 200, sessão ausente 401, CSRF 403,
inexistência 404, vínculo impedido 409, entrada inválida 422 e indisponibilidade 503.

## 6. Executar e conferir manualmente

Após revisar o destino do banco e reconstruir as imagens:

```sh
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check
```

Migrações não cadastram uma conta. Se necessário, provisione manualmente com
`docker compose exec backend python -m app.cli.auth create`; senha somente no prompt.
Não altere credenciais para reproduzir exemplos. Abra `http://localhost:3000/login`.

1. Crie duas unidades fictícias; busque, edite e confira os detalhes.
2. Cadastre colaboradora com unidade e outra sem unidade; confira filtros e equipe habitual.
3. Inative a unidade vinculada: confirme manutenção do vínculo e aviso; uma nova atribuição a ela deve falhar.
4. Na colaboradora, salve uma semana pendente, um dia incompleto e depois uma semana completa. Confira que subtotal e total se distinguem.
5. Configure 08:00–17:00 com intervalo 12:00–13:00: o dia completo deve representar 480 minutos. Saída anterior à entrada deve ser rejeitada.
6. Repita deliberadamente um dia para os dias escolhidos, salve e recarregue para conferir persistência.
7. Confira indicadores após alterações reais, mobile, teclado, logout e acesso direto sem sessão.

Este roteiro é de reprodução; não afirma que cada cenário já foi aprovado.

## 7. Validação e pendências

| Verificação | Situação documentada nesta atualização |
|---|---|
| CI final Sprint 02 | Aprovada no commit `df1dece`; evidência no início deste relatório. |
| Inspeção do protótipo | Dashboard, unidades e colaboradoras observados em desktop/mobile; limites no documento de referência. |
| Backend completo | 153 testes aprovados em PostgreSQL 17 descartável, container `recephub-sprint03-test-db`, banco `recephub_sprint03_test`. Um warning conhecido do TestClient permaneceu reportado. |
| Migrações e integridade | Upgrade/downgrade/upgrade, Alembic check e backfill aprovados na bateria: duas colaboradoras receberam 14 dias pendentes; sete constraints exercitadas. |
| API e transações | Cobertura de UUID inválido, ausência de sessão (401) e falha de PUT (503) com rollback sem substituição parcial da semana. |
| Ruff | Check e conferência final de formatação aprovados; 63 arquivos conferidos. |
| Frontend | ESLint, TypeScript e build aprovados. |
| Navegador | Primeira execução: 26 aprovados e dois com falha de seletor de alerta. Após corrigir a ambiguidade com o anunciador de rotas Next.js, os dois casos passaram em nova execução desktop/mobile (390×844). São 28 cenários cobertos; não houve uma única execução de 28 aprovados nesta evidência. |
| Revisão independente | `gpt-6-astra`, esforço xhigh: sem bloqueadores após correções do tratamento de UUID e navegação mobile; testes faltantes apontados na revisão foram acrescentados. |
| Validação visual local | Oito capturas desktop 1440×1000/mobile 390×844: dashboard, unidades, colaboradoras e editor semanal, sem overflow ou erros de página. Link de pular conteúdo visível por Tab. Capturas temporárias, não versionadas. |
| Indicadores reais | DOM/API conferidos: vazio → unidade ativa 1 → colaboradora ativa 1 → unidade inativa 0 preservando vínculo → desvinculação explícita e sem unidade 1. |
| Commits | Etapa 0 `9a68bd9`; etapa 1 `274d9a9`; etapa 2 `31c4021`; etapa 3 `782f69a`; etapa 4 `3a36b2b`; etapa 5 `3d9da95`. Etapa 6 e publicação em andamento. |
| CI Sprint 03 | Pendente de observação; não confundir com CI histórica da Sprint 02. |

Não foram adicionadas dependências de aplicação para os módulos operacionais. Manrope e
Sora foram incluídas como arquivos locais com licença OFL e avisos de terceiros. O problema
inicial de E2E era ambiguidade de `getByRole("alert")` com o anunciador Next.js; o seletor
foi delimitado ao aviso relevante, sem ocultar erros do produto.

Testes destrutivos exigem PostgreSQL descartável explícito, nome terminado em `_test`
e `TEST_DATABASE_ALLOW_RESET=1`. Não apontar para desenvolvimento ou reaproveitar o
antigo `recephub-test-db`. A existência de fixtures protegidas não dispensa conferir a URL.

## 8. Preparação da próxima sprint

Escalas por data, snapshots, ausências, cobertura mínima, exportações, comunicação e
IA continuam fora desta entrega. A próxima etapa deve partir de cadastros persistidos
e dias explicitamente configurados; nenhum dia pendente pode virar folga implicitamente.
Regras contratuais, turnos noturnos, publicação e ausências ainda exigem decisões próprias.
O encerramento remoto depende da publicação e da CI desta sprint. A integração e revisão
locais descritas acima estão aprovadas; requisitos futuros não são antecipados por essa aprovação.
