# Sprint 05 — relatório técnico de execução

Atualizado em 25/11/2026. Implementação, revisão, testes locais e conferência visual concluídos.
Publicação e CI remota pendentes de autenticação GitHub.

## Base e coordenação

A Sprint 04 foi salva em `db84f6f`, sem coautor, após 193 testes backend, 38 testes E2E,
Ruff, ESLint, TypeScript, build e conferência visual. O push encontrou ausência de
credencial GitHub utilizável. A branch da Sprint 05 parte desse commit local, aguardando
integração remota da base. Não há alegação de CI remota aprovada para nenhuma das duas.

Um subagente implementou ausências; outro, conflitos/cobertura; ambos implementaram suas
interfaces e cenários de navegador. O coordenador integrou migração, rotas, proxy,
navegação, diagnóstico da escala e ambiente isolado. Revisão independente gpt-6-astra
xhigh identificou melhorias de classificação e limite de duração, corrigidas e testadas.

## Arquivos e finalidade

| Arquivo/grupo | Responsabilidade |
|---|---|
| `backend/app/models/absence.py` | Ausência com versão e status; eventos com snapshot por versão |
| `backend/alembic/versions/0006_absences.py` | DDL congelado para tabelas, constraints e índices |
| `backend/app/schemas/absences.py` | Criação, patch, confirmação e filtros com validação cruzada |
| `backend/app/repositories/absences.py` | Busca e interseção de períodos |
| `backend/app/services/absences.py` | Edição atômica, bloqueios, eventos e cancelamento idempotente |
| `backend/app/api/v1/absences.py` | Contratos autenticados com defesas de escrita |
| `backend/app/services/absence_conflicts.py` | Interseção com trabalho efetivo, excluindo pausas |
| `backend/app/services/coverage.py`, `schemas/coverage.py`, `api/v1/coverage.py` | Prévia sem gravação e confirmação revalidada no servidor |
| `backend/app/services/schedules.py` | Incorporação dos conflitos na validação/publicação |
| `backend/app/models/__init__.py`, `api/v1/router.py` | Descoberta dos modelos e registro das rotas |
| `frontend/src/features/absences/`, `app/absences/` | Lista, filtros, formulário, detalhes, cancelamento e histórico |
| `frontend/src/features/coverage/coverage-panel.tsx` | Consulta e confirmação explícita de candidata |
| `frontend/src/features/schedules/schedules-client.tsx` | Integração do painel no conteúdo corrente |
| Proxy e navegação existentes | Lista restrita das novas rotas e acesso a Ausências |
| `backend/tests/test_absences.py`, `test_coverage.py` | Regras e integração dos novos serviços |
| `frontend/tests/e2e/absences.spec.ts`, `coverage.spec.ts` | Cenários preparados de navegador |
| `backend/app/api/v1/operational_alerts.py`, `frontend/src/features/dashboard/operational-alerts.tsx` | Ausências e alocações afetadas no período consultado; limites e nova tentativa |
| `backend/tests/test_absence_safety.py`, `test_absence_concurrency.py`, `test_operational_alerts.py` | Rollback, constraints, migração populada, duas conexões reais e contagens sem duplicação |

## Evidências observadas

- Primeira integração de ausências e migrações: 17 testes PostgreSQL aprovados.
- Regressões intermediárias: 224 e 246 testes aprovados, com um warning conhecido do
  TestClient, sem filtros para ocultá-lo.
- Regressão completa após integração: 256 aprovados. Inclui migrações, constraints,
  rollback de ausência/evento e cobertura/versão, preservação da revisão publicada,
  duas conexões reais na edição e concorrência entre ausência e publicação.
- Ajuste posterior no dashboard: oito testes específicos aprovados, incluindo pausa
  ocupando todo o turno (nenhum trabalho efetivo, nenhum conflito).
- ESLint, TypeScript e build integrado aprovados. Ruff check e formatação de 88 arquivos
  aprovados. Nenhuma dependência de aplicação adicionada.
- Bateria final: 50 cenários desktop/mobile aprovados em uma execução de 3,7 minutos;
  inclui regressão, formulários obsoletos preservados e indicadores após cancelamento.
- Revisão independente após correções: nenhum bloqueador P0/P1/P2 identificado.
- Conferência visual final em 25/11: seis capturas de lista, detalhes e consulta de cobertura
  em desktop 1440×1000/mobile 390×844. Sem overflow ou erros de página; foco por teclado,
  histórico America/Sao_Paulo, snapshot preservado e revisão somente leitura conferidos.
  Capturas temporárias, fora do Git. O roteiro foi corrigido para abrir explicitamente
  a revisão antes de verificar seu modo somente leitura.
- Fechamento documental local concluído. Publicação, PR e CI remota ainda pendentes.

Os dois primeiros testes de erro de formulário falharam por ambiguidade de `role=alert`
com o anunciador de rotas Next.js; os seletores foram limitados à mensagem esperada.
A execução inicial foi interrompida para corrigir e substituída por uma bateria completa.

## Correções da revisão

Cobertura passou a limitar a soma dos períodos existentes e propostos à duração conhecida,
descontando pausas. Ausência conhecida produz indisponibilidade mesmo sem dia congelado.
O painel preserva feedback após incremento da versão e oferece nova tentativa de unidades.
Histórico usa America/Sao_Paulo. Dashboard traz IDs de ausências na mesma consulta das
alocações, evitando falha se houver cancelamento concorrente; pausa ocupando todo turno
não gera conflito. Os testes de cada regra foram acrescentados antes do fechamento.

Banco backend `recephub_sprint05_test` e banco navegador `recephub_sprint05_browser_test`,
ambos descartáveis e separados dos anteriores, no PostgreSQL temporário já existente da
Sprint 04. API de navegador em loopback 3383; frontend de teste 3180. Fixtures de limpeza
operacional restritas ao nome exato do novo banco de navegador. Desenvolvimento intacto.

## Verificação manual futura

Após reconstruir as imagens e aplicar `alembic upgrade head` ao destino revisado, abra
`/absences`. Cadastre ausência integral e parcial fictícias; edite, consulte eventos e
cancele. Gere escala, publique e registre ausência posterior: a revisão anterior deve
permanecer igual e nova publicação exigir resolução do conflito. Consulte cobertura,
verifique motivos, confirme candidata e confira que somente o rascunho mudou.

Esse roteiro complementa os testes locais; CI remota permanece pendente. Credenciais e `.env.example`
preexistente permanecem fora dos commits. Sprint 06 ainda não iniciada.
