# RecepHub — Modelagem Inicial do Banco de Dados

**Versão:** 1.6
**Data:** 24/11/2026
**Status:** autenticação implementada; cadastros e horários concluídos; escalas semanais em implementação na Sprint 04. Ausências permanecem propostas.

## 1. Objetivo e princípios

Modelo PostgreSQL enxuto para **uma usuária**. Permite gerar escalas a partir das unidades e jornadas habituais, registrar exceções por data, gerenciar férias/folgas e publicar uma escala completa de modo consistente. Não usa tabela de guichês fixos, não armazena dados de pacientes e não exige persistência de e-mails ou mensagens de IA.

## 2. Tabelas implementadas e propostas

A Sprint 02 criou `users` e `user_sessions`. A Sprint 03 acrescenta `units`,
`employees` e `employee_work_patterns`, sem contas ou dados reais.
O antigo modelo diário foi substituído pelo semanal da Sprint 04. Ausências ainda não possuem migração.

### 2.1 `users`
- `id` UUID PK
- `username` VARCHAR(80) UNIQUE NOT NULL
- `password_hash` TEXT NOT NULL — Argon2id
- `active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMPTZ NOT NULL

Acrescentados `login_window_started_at` TIMESTAMPTZ NULL e `login_attempt_count`
SMALLINT NOT NULL DEFAULT 0. Contador limitado a 0–5; valor não zero exige início
de janela preenchido. O serviço implementa a janela compartilhada de 15 minutos,
reservando tentativas em transação curta com bloqueio da conta.
`created_at` tem default de banco `now()`; UUID é gerado pela aplicação.

Conta única, inclusive inativa: índice único `uq_users_single_account` sobre constante
`true`. Username corresponde a `^[a-z0-9._-]{3,80}$` com collation C; o banco rejeita
valores não canônicos. O serviço normaliza username antes de consultar/provisionar.
Provisionamento administrativo e hash Argon2id foram implementados na Etapa 2,
com comando interativo e sem conta/senha padrão. A migração continua sem seed.

### 2.2 `units`
- `id` UUID PK
- `name` VARCHAR(120) NOT NULL
- `city` VARCHAR(120) NULL
- `active` BOOLEAN NOT NULL DEFAULT TRUE
- `description` VARCHAR(500) NULL
- `updated_at` TIMESTAMPTZ NOT NULL

Nome não vazio; nomes iguais permitidos. Inativação lógica por `active`, sem DELETE.
`coverage_rules` não faz parte do esquema implementado.
- `created_at` TIMESTAMPTZ NOT NULL

A distribuição habitual **não** será interpretada automaticamente como cobertura mínima. Caso regras de cobertura ganhem complexidade, extrair para `staffing_requirements` por migração.

### 2.3 `employees`
- `id` UUID PK
- `display_name` VARCHAR(140) NOT NULL
- `home_unit_id` UUID NULL FK → `units.id`
- `notes` VARCHAR(500) NULL — observações operacionais
- `active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMPTZ NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL

A proposta inicial de JSONB foi substituída pela tabela normalizada aprovada na Sprint 03.
A FK opcional para unidade usa RESTRICT; inativar unidade preserva vínculos existentes.
Novos vínculos exigem unidade ativa. Nomes homônimos são permitidos.

### 2.3.1 `employee_work_patterns`

- `id` UUID PK; `employee_id` UUID FK → `employees.id` ON DELETE CASCADE.
- `weekday` inteiro de 0 (segunda) a 6 (domingo); único por colaboradora/dia.
- `state`: `pending`, `working` ou `non_working`.
- `start_time`, `end_time`, `break_start_time`, `break_end_time`: TIME opcionais, precisão de minuto, sem fuso.
- `created_at` e `updated_at`: TIMESTAMPTZ.

Sete dias são criados como pendentes para novas colaboradoras e preenchidos na migração
para cadastros anteriores. Estados pendente/sem trabalho não admitem horários. Jornada
incompleta pode ser salva; comparações conhecidas devem respeitar início/fim e intervalo
contido. Não há virada de dia. O PUT substitui a semana atomicamente sob bloqueio da
colaboradora. Subtotal soma dias completos; total semanal é nulo enquanto houver pendências.

No modelo atual, dia ausente nunca é interpretado como folga: a semana exige sete dias explícitos. Horários que cruzam meia-noite não são suportados.

### 2.4 `absences`
- `id` UUID PK
- `employee_id` UUID NOT NULL FK → `employees.id`
- `type` VARCHAR(40) NOT NULL — `VACATION`, `DAY_OFF`, `UNEXPECTED_ABSENCE`, `OTHER`
- `start_date` DATE NOT NULL
- `end_date` DATE NOT NULL
- `notes` TEXT NULL — evitar justificativas médicas ou dados sensíveis
- `created_at` TIMESTAMPTZ NOT NULL
- CHECK `start_date <= end_date`

As datas são inclusivas. Treinamento com presença em uma unidade é tratado inicialmente como posto/atividade da escala, não necessariamente ausência.

### 2.5 Escalas semanais — Sprint 04

- `schedules`: UUID, week_start DATE segunda-feira única, status draft/published, version,
  latest_revision_number, created_at e updated_at UTC.
- `schedule_employee_days`: UUID, schedule_id, employee_id, work_date, estado explícito
  pending/working/non_working/excluded, employee_name_snapshot, source_data JSONB,
  resolution_note opcional e timestamps. Único por escala/pessoa/data; excluído exige motivo.
- `schedule_assignments`: UUID, day_id, unit_id, unit_name_snapshot, entrada/saída,
  intervalo opcional completo, position textual até 80 caracteres e timestamps.
- `schedule_revisions`: UUID, schedule_id, number único por escala, source_version,
  schema_version, published_at e snapshot JSONB autocontido.

Cada participante recebe sete dias explícitos. Alocação deriva pessoa/data do dia;
períodos múltiplos não sobrepostos são permitidos, sem alterar o habitual. Datas dentro
da semana são validadas pelo serviço transacional, pois dependem da tabela pai.
Revisões preservam nomes e períodos; trigger rejeita UPDATE/DELETE comum. Publicar
novamente cria nova revisão. Não há DELETE público de histórico.

### 2.7 `user_sessions`

- `id` UUID PK, gerado pela aplicação.
- `user_id` UUID NOT NULL FK → `users.id` ON DELETE CASCADE, com índice.
- `token_hash` CHAR(64) UNIQUE NOT NULL, hexadecimal minúsculo; sem token original.
- `created_at` TIMESTAMPTZ NOT NULL DEFAULT now().
- `expires_at` TIMESTAMPTZ NOT NULL, posterior a `created_at`.
- `last_seen_at` TIMESTAMPTZ NOT NULL DEFAULT now(), maior ou igual a `created_at` e anterior a `expires_at`.
- `revoked_at` TIMESTAMPTZ NULL, quando preenchido maior ou igual a `created_at`.

Uma conta admite várias sessões independentes. Geração de token, SHA-256 e verificação
de validade/revogação foram implementadas nas Etapas 2–3 da Sprint 02. `TIMESTAMPTZ` representa instantes;
a apresentação do fuso depende da conexão, sem armazenar o nome de um fuso.

## 3. Semântica da escala-base e das exceções

POST explícito gera fotografia semanal; GET não materializa dados. Fontes incompletas,
unidade ausente/inativa e dias pendentes permanecem pendências. Remover período não
restaura automaticamente o habitual. Exclusão exige decisão e motivo operacional.
Mutações bloqueiam a escala e conferem expected_version. Publicação valida o conjunto,
cria snapshot e incrementa a revisão atomicamente. Edição posterior não modifica
publicações anteriores. Ausências futuras exigirão diagnóstico e revisão explícita.
Contratos: [Sprint 04](15-sprint-04.md). A proposta de adiar todo histórico ao pós-MVP
foi substituída na aprovação do planejamento integrado.

## 4. Relacionamentos

- `units` 1:N `employees` (origem habitual)
- `users` 1:N `user_sessions`, com exclusão em cascata
- `employees` 1:N `employee_work_patterns` (sete dias explícitos)
- `employees` 1:N `absences` (proposta)
- `schedules` 1:N `schedule_employee_days` e `schedule_revisions`
- `schedule_employee_days` 1:N `schedule_assignments`
- `employees` 1:N `schedule_employee_days`
- `units` 1:N `schedule_assignments`

## 5. Integridade e desempenho

- Índices: `schedules(week_start)` único, `schedule_employee_days(schedule_id, employee_id, work_date)` único, `schedule_assignments(day_id)`, `absences(employee_id, start_date, end_date)`.
- Validar `start_time < end_time` para turnos no mesmo dia; intervalo completo e contido no turno.
- Validar ausência, jornada e sobreposição **no backend em transação**. Usar bloqueio do registro de `schedules` ou mecanismo equivalente ao publicar/editar para reduzir corridas de atualização; cobrir com testes.
- Não impor exclusividade de posto textual até validar se múltiplas pessoas podem ocupar o mesmo setor/guichê em horários distintos.
- Horas previstas = duração do turno menos intervalo; não são ponto eletrônico nem folha de pagamento.
- Alertas do dashboard são calculados por consulta a `absences` e às escalas; não precisam de tabela própria no MVP.

## 6. IA e Outlook: sem novas tabelas obrigatórias

- **RF-14:** receber o texto da usuária, gerar assunto/corpo via adaptador de IA e devolver campos editáveis; não persistir o prompt ou o e-mail por padrão.
- **RF-15:** receber pedido em linguagem natural, produzir proposta estruturada, consultar IDs reais e validar; aplicar mudança à escala somente após confirmação autenticada.
- **RF-17:** usar `mailto:` e/ou abertura compatível do cliente de e-mail; os destinatários são preenchidos manualmente fora do app. Sem armazenar tokens do Outlook, mensagens enviadas ou credenciais Microsoft.
- Registros mínimos de erros técnicos não devem conter prompts com nomes reais, conteúdo de mensagens ou segredos.

## 7. Migrações e dados

- SQLAlchemy para entidades e consultas; Alembic para migrações incrementais.
- Datas operacionais em `America/Sao_Paulo`; `DATE` e `TIME` representam dia/horário local; auditoria em `TIMESTAMPTZ` (UTC no backend).
- Seed e testes com dados fictícios; credenciais e dados reais fora do Git.
- Backups protegidos e restauração testada; exclusão lógica de colaboradoras/unidades preservando histórico.

## 8. Evoluções pós-MVP

- `staffing_requirements` para cobertura por dia/faixa horária.
- Comparação detalhada e recuperação assistida; snapshots imutáveis já pertencem à Sprint 04.
- `employee_contracts` para múltiplos vínculos e regras com vigência.
- `push_subscriptions` e agendador para push notifications.
- Eventual tabela de modelos/rascunhos de comunicação, **somente se houver necessidade real de persistência**.

## 9. Decisões pendentes

- Jornadas reais e regras contratuais continuam a validar; a Sprint 03 permite configurar sete dias explicitamente e calcular minutos previstos. Viradas de dia exigem evolução futura.
- Regras e mínimos de cobertura; se há exceções justificáveis para impedimentos.
- Comportamento após editar uma escala já publicada e necessidade de identificar a última versão enviada.
- Autorização para uso de dados reais em infraestrutura pessoal.
