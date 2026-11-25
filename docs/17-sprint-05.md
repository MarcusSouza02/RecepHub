# Sprint 05 — ausências e cobertura

Atualizado em 25/11/2026. Estado: implementação, revisão, testes e conferência visual local aprovados;
publicação e CI de implementação aprovadas; entrega organizada no [PR #13 para dev](https://github.com/MarcusSouza02/RecepHub/pull/13).

Branch `feature/sprint-05-absences-coverage`, baseada no commit
`db84f6f` da Sprint 04. A base foi integrada pelo PR #12 em `dev 9e29d4b`. A implementação da Sprint 05 foi publicada
em `581cd91`, com cinco checks aprovados na execução 45591467156.

## Etapas e cards

| Card | Entrega | Estado |
|---|---|---|
| S05-01 | Modelo, migração e histórico de ausências | Implementado; testes PostgreSQL aprovados |
| S05-02 | API protegida, filtros, edição e cancelamento | Validado localmente |
| S05-03 | Interface responsiva de ausências | Validada em desktop/mobile |
| S05-04 | Conflitos de ausência na escala corrente | Validado, incluindo publicação concorrente |
| S05-05 | Consulta de candidatas e confirmação de cobertura | Validado e revisado |
| S05-06 | Dashboard e homologação integrada | 256 testes backend e 50 E2E aprovados |
| S05-07 | Relatório, revisão final, commit e CI | Commit, revisão e CI de implementação aprovados; PR #13 para dev |

## Regras e contratos

Ausências operacionais aceitam férias (`vacation`), folga (`day_off`), compensação
(`compensation`) e outro (`other`). Não se cadastram informações clínicas. Dias inteiros
incluem as duas datas; ausências parciais exigem uma única data e início anterior ao fim,
sem atravessar meia-noite. Observações têm até 500 caracteres.

Sobreposições são permitidas e sinalizadas; o mesmo impedimento não é contado duas vezes.
Edição exige versão atual. Cancelar exige confirmação, preserva o registro e seu histórico;
repetir cancelamento não cria eventos ou incrementos adicionais. A colaboradora não muda
na edição. Cadastros inativos continuam consultáveis e podem receber registro operacional.

Rotas autenticadas sob `/api/v1`:

- `GET/POST /absences`, `GET/PATCH /absences/{id}`;
- `POST /absences/{id}/cancel`, `GET /absences/{id}/events`;
- `POST /schedules/{id}/coverage/preview` e `/coverage/confirm`.

Listas aceitam colaboradora, tipo, status `active|cancelled|all`, período e paginação
20/100. Escritas reutilizam origem exata, CSRF, JSON, limite 4 KiB e respostas sem cache.

Ausência ativa que intercepta trabalho efetivo produz diagnóstico na escala corrente e
bloqueia nova publicação. Uma ausência inteiramente dentro do intervalo não conflita.
Revisões já publicadas permanecem intactas.

A prévia de cobertura não altera a escala. Classificações: disponível, indisponível ou
informação insuficiente, com motivos explícitos e ordem neutra por nome/UUID. A referência
é o horário congelado na geração, com desconto do intervalo; cadastro habitual alterado
posteriormente não redefine essa referência. Dia ausente ou pendente não significa livre.
Não se sugere período fora da jornada conhecida ou tempo adicional acima de seu total.

Confirmar exige intenção explícita e versão da escala; o servidor recalcula candidatas,
ausências, unidades e alocações sob bloqueios antes de adicionar ao rascunho. Não remove
a alocação da pessoa ausente nem publica automaticamente. A resolução original continua
explícita no editor da escala.

## Aceite

Testar persistência, eventos, cancelamento, versões obsoletas, sobreposição, pausas,
preservação de publicações, preview sem gravação, revalidação da confirmação e rollback.
Executar migrações somente em banco descartável para ciclos destrutivos; executar
regressão backend, Ruff, frontend, navegador desktop/mobile e observar CI após publicação.
Ausência de evidência deve permanecer registrada como pendência.
