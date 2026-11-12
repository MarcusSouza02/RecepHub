# RecepHub — Modelagem Inicial do Banco de Dados

**Versão:** 1.4
**Data:** 12/11/2026
**Status:** Persistência e serviços de autenticação implementados na Sprint 02. Demais entidades são propostas; regras de jornada e cobertura pendentes de validação.

## 1. Objetivo e princípios

Modelo PostgreSQL enxuto para **uma usuária**. Permite gerar escalas a partir das unidades e jornadas habituais, registrar exceções por data, gerenciar férias/folgas e publicar uma escala completa de modo consistente. Não usa tabela de guichês fixos, não armazena dados de pacientes e não exige persistência de e-mails ou mensagens de IA.

## 2. Tabelas previstas (7)

Somente `users` e `user_sessions` possuem modelos e migração nesta entrega. A revisão
`0001_auth_foundation` não cria as outras cinco tabelas nem cadastra uma conta.

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
- `coverage_rules` JSONB NULL — **opcional**, estrutura versionada/validada, apenas quando a regra de cobertura for definida
- `created_at` TIMESTAMPTZ NOT NULL

A distribuição habitual **não** será interpretada automaticamente como cobertura mínima. Caso regras de cobertura ganhem complexidade, extrair para `staffing_requirements` por migração.

### 2.3 `employees`
- `id` UUID PK
- `display_name` VARCHAR(140) NOT NULL
- `home_unit_id` UUID NULL FK → `units.id`
- `regular_schedule` JSONB NOT NULL DEFAULT '{}'::jsonb — dias, entrada, saída e intervalo usuais, validados por Pydantic
- `active` BOOLEAN NOT NULL DEFAULT TRUE
- `created_at` TIMESTAMPTZ NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL

Exemplo **fictício** de `regular_schedule` (formato provisório):

```json
{
  "mon": {"start": "07:00", "end": "16:00", "break_start": "11:00", "break_end": "12:00"},
  "tue": {"start": "07:00", "end": "16:00", "break_start": "11:00", "break_end": "12:00"},
  "sat": {"start": "08:00", "end": "12:00", "break_start": null, "break_end": null}
}
```

Dias não presentes são considerados sem jornada habitual. Horários que cruzam meia-noite exigirão decisão explícita antes de suporte.

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

### 2.5 `schedule_days`
- `id` UUID PK
- `work_date` DATE UNIQUE NOT NULL
- `status` VARCHAR(20) NOT NULL DEFAULT 'DRAFT' — `DRAFT` ou `PUBLISHED`
- `published_at` TIMESTAMPTZ NULL
- `created_at` TIMESTAMPTZ NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL

É o **cabeçalho de uma escala completa do dia**, de todas as unidades. Controla publicação atômica, inclusive quando alguma unidade não tiver alocações. Na geração inicial, o backend materializa uma fotografia da escala-base daquele dia para edição; dias ainda não materializados são calculados da configuração habitual e das ausências. Publicação não equivale a envio a terceiros.

### 2.6 `schedule_assignments`
- `id` UUID PK
- `schedule_day_id` UUID NOT NULL FK → `schedule_days.id` ON DELETE CASCADE
- `employee_id` UUID NOT NULL FK → `employees.id`
- `unit_id` UUID NOT NULL FK → `units.id`
- `start_time` TIME NOT NULL
- `end_time` TIME NOT NULL
- `break_start_time` TIME NULL
- `break_end_time` TIME NULL
- `position` VARCHAR(80) NULL — posto textual dinâmico, como `Guichê 2`, `Triagem`, `Unimed`, `Treinamento`
- `created_at` TIMESTAMPTZ NOT NULL
- `updated_at` TIMESTAMPTZ NOT NULL

São as **linhas concretas** da escala do dia materializado. Não são geradas antecipadamente para todos os dias futuros. Uma remoção excepcional é representada pela ausência daquela linha no snapshot explícito do dia — nunca pela exclusão da jornada habitual no cadastro.

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

1. **Dia sem `schedule_days`:** gerar visualização virtual da escala-base a partir de `employees.home_unit_id`, `regular_schedule` e `absences`.
2. **Primeira alteração:** criar `schedule_days` e suas `schedule_assignments` com uma fotografia da base; aplicar a mudança à fotografia.
3. **Dia já materializado:** usar somente suas linhas concretas, inclusive se alguma colaboradora tiver sido removida. Não reconstruir automaticamente linhas excluídas.
4. **Nova ausência sobre escala existente:** detectar conflito e exigir resolução antes da publicação. Não remover silenciosamente alocações que a usuária já ajustou.
5. **Publicação:** validar o conjunto inteiro, atualizar `schedule_days.status` em transação e expor a versão publicada nas exportações. Edição posterior pode retornar o dia a `DRAFT`, segundo política a validar; o histórico completo de versões fica pós-MVP.
6. **Atualização de jornada habitual:** vale para os dias ainda não materializados. Dias materializados não são reescritos sem escolha explícita.

O modelo original de seis tabelas, agora acrescido de `user_sessions`, evita a ambiguidade entre “nenhuma exceção” e “retirada deliberada da escala”. A definição operacional de publicação e edição de uma escala já publicada deverá ser validada com a usuária.

## 4. Relacionamentos

- `units` 1:N `employees` (origem habitual)
- `users` 1:N `user_sessions`, com exclusão em cascata
- `employees` 1:N `absences`
- `schedule_days` 1:N `schedule_assignments`
- `employees` 1:N `schedule_assignments`
- `units` 1:N `schedule_assignments`

## 5. Integridade e desempenho

- Índices: `schedule_days(work_date)` único, `schedule_assignments(schedule_day_id, unit_id)`, `schedule_assignments(schedule_day_id, employee_id)`, `absences(employee_id, start_date, end_date)`.
- Validar `start_time < end_time` para turnos no mesmo dia; intervalo completo e contido no turno.
- Validar ausência, jornada e sobreposição **no backend em transação**. Usar bloqueio do registro de `schedule_days` ou mecanismo equivalente ao publicar/editar para reduzir corridas de atualização; cobrir com testes.
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
- `schedule_versions` e auditoria detalhada para histórico imutável e recuperação de versões.
- `employee_contracts` para múltiplos vínculos e regras com vigência.
- `push_subscriptions` e agendador para push notifications.
- Eventual tabela de modelos/rascunhos de comunicação, **somente se houver necessidade real de persistência**.

## 9. Decisões pendentes

- Jornada de segunda a sábado, intervalos e eventuais viradas de dia.
- Regras e mínimos de cobertura; se há exceções justificáveis para impedimentos.
- Comportamento após editar uma escala já publicada e necessidade de identificar a última versão enviada.
- Autorização para uso de dados reais em infraestrutura pessoal.
