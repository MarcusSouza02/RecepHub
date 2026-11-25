# Sprint 04 — relatório técnico

Atualização: 24/11/2026. Estado: implementação, revisão e testes automatizados locais
concluídos; publicação e CI em andamento. Este registro distingue resultados observados de pendências.

## Base, escopo e coordenação

Branch `feature/sprint-04-schedules`, a partir de `dev e4b1fd4`. A Sprint 03 já estava
integrada e com [CI aprovada](https://github.com/MarcusSouza02/RecepHub/actions/runs/45486371431);
seus estados documentais desatualizados foram corrigidos nesta entrega.

O usuário aprovou o planejamento integrado e execução coordenada, com branches separadas,
subagentes e commits sem coautor. Um agente implementou persistência/migração e testes
de segurança/concorrência; outro, API e serviços; outro, frontend e E2E. O coordenador
definiu contratos, integrou modelos/rotas/proxy, isolou bancos, executou testes e corrigiu
documentação. Revisão independente por gpt-6-astra xhigh examinou os arquivos reais.

Não foram alterados `.env`, credenciais, dados de desenvolvimento ou produção. A mudança
preexistente de `.env.example` permanece excluída dos commits. Nenhuma conta real foi criada.

## Comportamento entregue

- Uma escala por semana de segunda a domingo, gerada explicitamente a partir dos cadastros.
- Sete dias por participante, mantendo pendências, dias sem trabalho e fontes incompletas.
- Nomes e dados habituais fotografados; edição posterior do cadastro não regenera a escala.
- Alocações efetivas por data, vários períodos não sobrepostos, unidade e atividade livres.
- Remoção de período não apaga jornada habitual nem restaura automaticamente a base.
- Estado excluído exige motivo operacional; não equivale a folga, férias ou compensação.
- Versão esperada e bloqueio transacional: edição obsoleta retorna 409 sem sobrescrita.
- Publicação confirmada e atômica; revisões numeradas, autocontidas e imutáveis no PostgreSQL.
- Edição posterior retorna o conteúdo corrente a rascunho e preserva publicações anteriores.
- Histórico somente leitura, filtros por unidade/data e interface responsiva.

Não foram antecipadas ausências/cobertura (Sprint 05), exportação/comunicação/IA (06),
regras trabalhistas, mínimos de equipe ou exclusividade de posto. Comparação lado a lado
de revisões (S04-09, P2) fica adiada; consulta individual de todas as revisões foi implementada.

## Arquivos e responsabilidades

| Arquivo ou grupo | Implementação |
|---|---|
| backend/app/models/schedule.py | Schedule, ScheduleEmployeeDay, ScheduleAssignment e ScheduleRevision; FKs, índices, unicidade e checks. |
| backend/alembic/versions/0005_schedules.py | Quatro tabelas encadeadas à 0004; trigger impede UPDATE/DELETE comum de revisões; downgrade remove objetos na ordem correta. |
| backend/app/models/__init__.py | Registro de modelos para metadados e Alembic. |
| backend/app/schemas/schedules.py | Datas, semana válida, versão estrita, horários locais completos, estado/resolução e confirmação booleana explícita. |
| backend/app/services/schedules.py | Geração, consultas, edição, validação de sobreposição, estados, publicação e leitura histórica. |
| backend/app/api/v1/schedules.py | Endpoints protegidos, validação sanitizada, CSRF/JSON/4 KiB e códigos HTTP. |
| backend/app/api/v1/router.py | Registro do módulo versionado. |
| backend/tests/test_schedule_models.py | Semana única, constraints de horários, exclusão motivada e imutabilidade das revisões. |
| backend/tests/test_schedules.py | Geração congelada, duplicação, edição, publicação, pendências e nomes preservados inclusive com payload real da interface. |
| backend/tests/test_schedule_safety.py | Autenticação, CSRF, UUID, isolamento entre escalas, versão obsoleta, histórico e rollback após falha de commit. |
| backend/tests/test_schedule_concurrency.py | Duas conexões reais disputam a mesma versão: um sucesso, um 409 e incremento único. Limpeza apenas de UUIDs fictícios próprios. |
| backend/tests/e2e_admin.py | Reset das tabelas operacionais apenas no novo banco de navegador explicitamente autorizado; preserva trigger na aplicação comum. |
| frontend/src/app/schedules/page.tsx e [id]/page.tsx | Entradas de servidor protegidas por requireSession. |
| frontend/src/features/schedules/types.ts | DTOs do contrato de escala, estados, alocações, diagnóstico e revisão. |
| frontend/src/features/schedules/schedules-client.tsx | Lista/geração, filtros, editor, descarte, resolução, confirmação de publicação e histórico readonly. |
| frontend/src/app/api/v1/[...path]/route.ts | Allowlist de paths/métodos/UUIDs/revisões/parâmetros da escala; mantém proteções existentes. |
| frontend/src/features/dashboard/navigation.tsx | Navegação Escalas no shell existente, com quebra no mobile. |
| frontend/tests/e2e/schedules.spec.ts | Geração/edição/publicação/histórico, pendências, formulário obsoleto, filtros e proteção de acesso. |
| .github/workflows/ci.yml | Banco e container exclusivos Sprint 04 no job browser; preserva os cinco jobs. |
| docs/04, docs/05, docs/14, docs/15 e README | Modelagem semanal, ADR, encerramento histórico da Sprint 03, quadro atual e instruções. |

## Conceitos e transações

Schedule controla a versão do agregado. Estados diários distinguem ausência de informação
de dia explicitamente sem trabalho e retirada deliberada. Assignment deriva pessoa/data
do dia e representa somente o período concreto. Revision contém snapshot JSONB com nomes,
estados e períodos, sem reconstrução a partir de cadastros atuais.

Mutações bloqueiam Schedule FOR UPDATE e conferem expected_version. Detalhes usam bloqueio
compartilhado para não combinar versão e linhas de edições diferentes. Geração bloqueia
as fontes necessárias; publicação revalida cadastros e períodos antes do commit único.
Turnos adjacentes são permitidos; sobreposição considera todo o turno, inclusive pausa.
Leituras históricas não incorporam renomeações, inativações ou futuras ausências.

## Verificações observadas

| Verificação | Resultado |
|---|---|
| Backend PostgreSQL 17 | 193 testes aprovados, inclusive regressões das Sprints 01–03. Bateria repetida após correções da revisão: 193 aprovados. |
| Warning backend | StarletteDeprecationWarning conhecido sobre httpx/TestClient, sem filtro para ocultá-lo. |
| Migrações | Upgrade/downgrade/upgrade e Alembic check exercitados na bateria completa contra banco descartável. |
| Concorrência | Duas Sessions/conexões reais: um 200, um 409, conteúdo do vencedor e versão incrementada uma vez. |
| Falha transacional | Commit simulado falha após flush; resposta 503 sanitizada e fechamento da sessão desfaz revisão/versão/conteúdo parcial. |
| Ruff | Check e formatação aprovados em 72 arquivos. |
| Frontend | ESLint, TypeScript e build aprovados; build final ajusta acentos, filtros e rótulo do conteúdo publicado. |
| Navegador | 38 testes aprovados em uma execução completa de 5,3 minutos, nos projetos desktop e mobile; dez cenários novos de escalas e 28 de regressão. |
| Conferência visual | Seis capturas de lista, rascunho e revisão em desktop 1440×1000/mobile 390×844; sem overflow ou erros de página. Foco inicial no link de pular conteúdo e revisão somente leitura confirmados. Capturas temporárias, fora do Git. |
| CI remota | Pendente de publicação e observação desta entrega. |

Ambiente isolado: rede `recephub-sprint04-tests`, PostgreSQL temporário
`recephub-sprint04-test-db`, banco backend `recephub_sprint04_test` e banco navegador
`recephub_sprint04_browser_test`. API de navegador em loopback porta 3382, frontend 3180.
Os bancos anteriores e o banco de desenvolvimento não foram reutilizados ou apagados.

A primeira tentativa de navegador encontrou o Chromium ausente no ambiente. Após instalar
o navegador do Playwright, a bateria completa passou. Tentativas interrompidas durante
essa preparação não foram contabilizadas como aprovação.

## Revisão e correções

O revisor apontou três problemas P2, corrigidos antes do aceite:

1. Formulário aberto podia permanecer na visão histórica: troca bloqueada durante edição,
   formulários condicionados ao conteúdo corrente e mutação defensivamente bloqueada.
2. Filtro de unidade selecionava dias, mas mostrava períodos de outras unidades: agora
   filtra também as linhas, inclusive no histórico; E2E cobre duas unidades no mesmo dia.
3. PATCH com a mesma unidade podia atualizar seu nome congelado: snapshot só muda quando
   o UUID da unidade muda; teste reproduz o payload efetivo da interface após renomeação.

Limites extremos de data foram tratados para evitar overflow. Confirmação exige booleano
true, horários numéricos são rejeitados e erro de geração concorrente vira 409. Textos com
acentos e rótulo publicado/rascunho foram corrigidos antes do build final. Não houve nova
dependência de aplicação.

## Executar e homologar manualmente

Depois de atualizar o código e revisar o destino do banco:

```sh
docker compose up --build -d
docker compose exec backend alembic upgrade head
docker compose exec backend alembic current
docker compose exec backend alembic check
```

Abra `/schedules` com sua conta existente. Migração não cria conta nem altera senha.

1. Configure cadastros fictícios e uma semana habitual completa ou parcialmente pendente.
2. Gere uma segunda-feira e confirme os sete dias; tentar novamente não duplica a semana.
3. Edite unidade, período e atividade; confira que o habitual permaneceu intacto.
4. Resolva pendências explicitamente; retirada exige motivo. Remover o último período
   não transforma o dia automaticamente em folga.
5. Valide e publique; consulte revisão 1. Edite o conteúdo corrente e publique revisão 2.
6. Renomeie um cadastro e confira que a revisão 1 mantém seus nomes e horários.
7. Abra dois navegadores e edite a mesma versão: o segundo deve receber 409, com formulário
   preservado e necessidade de recarga explícita.

Testes destrutivos exigem TEST_DATABASE_URL terminado em `_test` e
TEST_DATABASE_ALLOW_RESET=1; nunca executar downgrade no desenvolvimento para testar.

## Preparação da Sprint 05

Ausências e confirmação de cobertura reutilizarão estados diários, validator e comandos
versionados. Nova ausência após publicação produzirá diagnóstico separado, sem editar
snapshot. Propostas futuras de IA também alterarão somente rascunho confirmado. O formato
snapshot versionado permite exportação posterior sem consultar nomes mutáveis.
