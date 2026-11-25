# Sprint 04 — escalas semanais, publicação e histórico

Data de início: 24/11/2026. Estado: concluída e integrada em `dev` em 25/11/2026 pelo PR #12, após CI aprovada.

## Base e autorização

O planejamento integrado das Sprints 04–06 foi aprovado para execução. O coordenador
distribui etapas entre subagentes e centraliza contratos, migrações, integração, revisão
e Git. Branch desta sprint: `feature/sprint-04-schedules`, baseada em `dev e4b1fd4`.
Os commits são autorizados, sem coautor, preservando `.env` e a mudança preexistente
de `.env.example`. Deploy e integração em `main` não fazem parte desta entrega.

A Sprint 03 foi integrada pelos PRs 3–9; a árvore de `e4b1fd4` equivale a `40a563e`.
[CI de dev aprovada](https://github.com/MarcusSouza02/RecepHub/actions/runs/45486371431).
Resultados históricos não substituem a validação da Sprint 04.

## Decisões e comportamento

- Uma escala por semana, segunda a domingo, com datas operacionais locais e auditoria UTC.
- Quatro entidades: `Schedule`, `ScheduleEmployeeDay`, `ScheduleAssignment`, `ScheduleRevision`.
- Sete dias explícitos por participante, com estados: `pending`, `working`, `non_working` ou `excluded`.
- Exclusão deliberada exige motivo operacional e não significa folga ou ausência.
- Fontes e nomes são fotografados na geração; mudanças cadastrais não regeneram o rascunho.
- Pessoas ativas são participantes iniciais. Jornada completa e unidade ativa geram alocação;
  dados incompletos, sem unidade ou unidade inativa geram pendência com a fonte preservada.
- Uma pessoa pode ter vários períodos sem sobreposição no dia. O habitual não é alterado.
- Atividade/posto é texto opcional da alocação, sem cadastro fixo ou exclusividade presumida.
- Períodos no mesmo dia, precisão de minuto, intervalo opcional completo e contido.
- Conflitos consideram todo o turno, inclusive pausa; limites adjacentes são permitidos.
- Pessoa/unidade inativada não é apagada da fotografia; uma publicação exige resolução.
- Pendências e dias de trabalho sem alocação impedem publicação. Resolver é ação explícita.
- Edição posterior mantém a revisão anterior e torna o conteúdo corrente um novo rascunho.
- Publicação confirmada cria snapshot JSONB autocontido, numerado e imutável.
- Edição/publicação exigem `expected_version`; versão obsoleta retorna 409.
- Nenhum GET gera ou publica escala. Criar novamente a mesma semana retorna 409.

Ausências e cobertura entram somente na Sprint 05; exportação, comunicação e IA na 06.
Não se inferem mínimos de pessoal, direitos trabalhistas, disponibilidade ou regras de saúde.

## Cards e responsáveis

| Card | Etapa | Entrega | Dependência | Responsável |
|---|---|---|---|---|
| S04-01 | 0 | Consolidar base, regras e contratos | Sprint 03 | Coordenador |
| S04-02 | 1 | Modelos, constraints, migração e testes | 01 | Agente persistência |
| S04-03 | 2 | Geração determinística e estados diários | 02 | Agente backend |
| S04-04 | 2 | API de edição versionada e proxy | 03 | Backend/coordenador |
| S04-05 | 3 | Lista e visões por unidade/dia | Contrato 04 | Agente frontend |
| S04-06 | 3 | Editor, resolução, remoção e descarte | 04/05 | Agente frontend |
| S04-07 | 4 | Validação e publicação transacional | 04 | Agente backend |
| S04-08 | 4 | Histórico e nova revisão | 07 | Backend/frontend |
| S04-09 | 4 | Comparação simples de revisões (P2) | 08 | Após núcleo P0 |
| S04-10 | 5 | Homologação, revisão independente e relatório | Todos P0 | Coordenador/revisor |

Todos os cards são P0 exceto S04-09. Testes acompanham cada incremento; resultado e
limitações serão consolidados em `16-sprint-04-relatorio-tecnico.md`. Nenhuma migração
será executada em paralelo no mesmo banco.

## Contratos congelados

Todos sob `/api/v1`, com sessão no FastAPI, `no-store` e escritas com Origin/CSRF/JSON
e 4 KiB no proxy e API. UUIDs, métodos e parâmetros entram explicitamente na allowlist.

| Método/caminho | Entrada e resultado |
|---|---|
| GET /schedules | from_date, to_date, page, page_size; lista paginada de resumos |
| POST /schedules | week_start; cria fotografia semanal |
| GET /schedules/{id} | Conteúdo corrente, versão, dias e diagnósticos |
| POST /schedules/{id}/assignments | expected_version, day_id, unidade, horários, atividade |
| PATCH /schedules/{id}/assignments/{assignment_id} | expected_version e campos editáveis |
| POST /schedules/{id}/assignments/{assignment_id}/remove | expected_version |
| PATCH /schedules/{id}/days/{day_id} | expected_version, state, resolution_note |
| POST /schedules/{id}/validate | expected_version; diagnóstico sem publicação |
| POST /schedules/{id}/publish | expected_version, confirmed=true; revisão publicada |
| GET /schedules/{id}/revisions | Lista de revisões |
| GET /schedules/{id}/revisions/{number} | Revisão e snapshot imutável |

Resumo: id, week_start, status, version, latest_revision_number, created_at, updated_at.
Detalhe acrescenta days e diagnostics. Cada dia traz id, employee_id, employee_name,
work_date, state, resolution_note, source_data e assignments. Alocação traz id, unit_id,
unit_name, start_time, end_time, break_start_time, break_end_time e position.
Diagnósticos: errors/warnings com code, message e identificadores relevantes.
Revisão: id, number, source_version, schema_version, published_at e snapshot.

## Integridade e concorrência

Semana única, dia único por pessoa/escala/data, FKs explícitas e checks temporais.
Datas dentro da semana são validadas transacionalmente, pois CHECK não faz JOIN.
Alocação deriva pessoa/data do dia. Revisões não admitem UPDATE/DELETE comum; trigger
de banco protege o snapshot. Downgrade administrativo é testado somente em banco descartável.
Mutação bloqueia Schedule, confere versão e aplica tudo ou nada; bloqueios cadastrais
necessários têm ordem estável. Falhas e repetição não podem gerar publicação parcial.

## Aceite e validação

- Gerar e reabrir semana sem alterar habitual nem restaurar remoções automaticamente.
- Preservar pendências, sem unidade, unidades inativas e dias sem trabalho.
- Editar horários, unidade e atividade; resolver estados explicitamente.
- Rejeitar sobreposição e publicação incompleta; testar versões obsoletas e rollback.
- Publicar revisão 1, editar e publicar revisão 2; nomes/horários da 1 permanecem iguais.
- Constraints, upgrade/downgrade/upgrade e Alembic check em PostgreSQL descartável.
- Sessão, CSRF, 4 KiB, UUIDs, isolamento entre recursos e erros sanitizados.
- Desktop/mobile 390px, teclado, descarte, carregamento, vazio, erro e histórico readonly.
- Regressão das Sprints 01–03, Ruff, ESLint, TypeScript, build, E2E e CI observada.

## Preparação das Sprints 05 e 06

O validador e os comandos de rascunho serão reutilizados por ausências/cobertura e por
propostas confirmadas. Snapshot versionado alimentará exportação sem consultar nomes
atuais. Não há tabelas especulativas de ausência/IA nesta migração. Revisões publicadas
não serão reescritas por ausências posteriores. Os documentos 17–20 serão produzidos
nos respectivos incrementos, mantendo o planejamento integrado aprovado.
