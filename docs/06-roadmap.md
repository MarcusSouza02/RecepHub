# RecepHub — Roadmap e Plano de Execução

**Versão:** 1.1  
**Data:** 29/10/2026  
**Status:** Planejamento incremental atualizado para incluir RF-14, RF-15 e RF-17 no MVP.

## 1. Estratégia de entrega

A **primeira versão completa do MVP** inclui escalas e cadastros, assistente de IA para comunicados e interpretações de alterações, além da abertura de rascunhos no cliente de e-mail. Para diminuir risco, os recursos serão implementados em marcos independentes; operações centrais deverão funcionar sem IA. Nenhum recurso exige plano pago obrigatório.

## 2. Marco 0 — Descoberta e validação

- [x] Definir visão do produto, stack e custo inicial zero.
- [x] Criar seis documentos iniciais.
- [x] Confirmar uma única usuária, unidades e horários habituais, exceções e prioridade da visão por unidade.
- [x] Incluir RF-14, RF-15 e RF-17 no MVP.
- [ ] Validar dias/horários habituais, intervalos e sábados.
- [ ] Confirmar critérios mínimos de cobertura (não inferir do quadro habitual).
- [ ] Definir comportamento de escala editada após publicação e tratamento de treinamento.
- [ ] Validar autorização e fluxo de utilização de dados reais.
- [ ] Aprovar layout de exportação e identidade visual própria.

**Entregável:** regras operacionais e critérios de aceite validados.

## 3. Marco 1 — Fundação

**Recorte aprovado para a Sprint 01:** infraestrutura, página provisória, saúde da API e do banco,
Alembic, qualidade e estrutura inicial do PWA. Autenticação permanece como etapa posterior deste
marco; a Sprint 01 não entrega ainda o login protegido. Manifest e ícones serão iniciados agora,
com homologação final no Marco 6. Detalhes em [Sprint 01](07-sprint-01.md).

- [ ] Repositório GitHub, README, licença, `.gitignore`, `.env.example` e estrutura `docs/`.
- [x] Frontend Next.js + TypeScript + Tailwind + shadcn/ui.
- [x] Backend FastAPI + SQLAlchemy + Alembic, PostgreSQL e Docker Compose.
- [x] Estruturar módulos e testes básicos.
- [ ] Login único, hash Argon2id, sessão segura, autenticação dos endpoints.
- [x] GitHub Actions configurado com lint, testes e build (execução remota pendente).

**Entregável:** aplicação local com login protegido.

## 4. Marco 2 — Dados e escala habitual

- [ ] CRUD de unidades e colaboradoras, incluindo inativação.
- [ ] Vincular unidade de origem e jornada habitual por dia da semana.
- [ ] Registrar férias/folgas/ausências diretamente, sem aprovação.
- [ ] Visualizar distribuição habitual por unidade e por data.
- [ ] Criar seed fictícia, migrações e testes de integridade.

**Entregável:** cadastro e visão operacional base.

## 5. Marco 3 — Escalas, exceções e dashboard

- [ ] Calcular a escala-base a partir de jornada habitual e ausências.
- [ ] Criar snapshot por data ao editar, sem alterar o cadastro habitual.
- [ ] Alterar unidade, posto e horário; remover colaboradora da escala do dia.
- [ ] Validar conflito de horários e ausências antes da publicação.
- [ ] Publicar escala inteira por data com confirmação explícita.
- [ ] Criar visualização prioritária por unidade, tabela e calendário semanal.
- [ ] Calcular horas previstas, alertar férias/folgas futuras e indicar cobertura quando houver parâmetros.
- [ ] Exportar escala publicada em PNG e PDF; compartilhamento manual no dispositivo.

**Entregável:** núcleo operacional do MVP funcional sem IA.

## 6. Marco 4 — Comunicação e Outlook simplificado (RF-17)

- [ ] Tela de elaboração de comunicado com assunto e corpo editáveis.
- [ ] Ação de copiar conteúdo.
- [ ] Abrir composição via `mailto:` / cliente padrão; selecionar destinatários manualmente.
- [ ] Testar Outlook Desktop, Outlook Web e mobile conforme os dispositivos disponíveis; fornecer fallback se não abrir.
- [ ] Garantir que o sistema não armazene senhas/tokens de e-mail nem faça envio automático.

**Entregável:** comunicação manual pronta, mesmo sem IA.

## 7. Marco 5 — Assistente de IA (RF-14 e RF-15)

- [ ] Abstrair `AIProvider` e adicionar adaptador Gemini gratuito, após confirmar limites e privacidade.
- [ ] RF-14: gerar assunto/corpo, permitir edição, copiar e abrir no cliente de e-mail.
- [ ] RF-15: interpretar solicitação, produzir JSON validado, resolver IDs e construir preview.
- [ ] Verificar conflitos, disponibilidade, jornada e cobertura no backend; confirmar antes de salvar.
- [ ] Garantir que salvar a proposta não publique automaticamente a escala.
- [ ] Implementar erros amigáveis, timeout, limites de uso e fallback manual.
- [ ] Mockar respostas da IA nos testes, incluindo ambiguidade e instruções inesperadas.

**Entregável:** MVP assistido completo, sem dependência obrigatória da IA.

## 8. Marco 6 — PWA, deploy e homologação da primeira versão

- [ ] Manifest, ícones e responsividade final.
- [ ] Deploy frontend Vercel Hobby, API Render Free, banco Supabase Free (rever condições vigentes).
- [ ] Configurar segredos, HTTPS, CORS, cookies/sessão em domínios reais e proteção CSRF aplicável.
- [ ] Testar backup/restauração e tratar backend adormecido ou banco pausado.
- [ ] Validar login, escalas, exportação, e-mail e assistente IA em computador e celular.
- [ ] Revisar segurança e privacidade antes de qualquer uso de dados reais.

**Entregável:** primeira versão PWA instalável e utilizável.

## 9. Backlog pós-MVP

- [ ] **RF-16:** sugestões avançadas de cobertura e eventual OR-Tools.
- [ ] **RF-18:** WhatsApp Business oficial, somente se fizer sentido e for viável.
- [ ] **RF-19:** versões históricas imutáveis, rollback e relatórios.
- [ ] **RF-24:** push notifications com agendador e inscrições dos dispositivos.
- [ ] **RF-25:** integração autenticada Outlook/Microsoft Graph se autorizada e necessária.
- [ ] **RF-26:** múltiplos usuários e permissões caso o escopo seja ampliado.

## 10. Definition of Done

Cada entrega deve ter critério de aceite, testes das regras críticas, interface responsiva, ausência de segredos/dados reais no repositório, documentação atualizada e validação da usuária quando aplicável. Para IA, adicionar: schema validado, confirmação humana, proteção de dados e fallback manual. Para Outlook, verificar que **nenhum envio ocorre dentro do RecepHub**.

## 11. Riscos e mitigação

| Risco | Mitigação |
|---|---|
| Divergências nas regras de jornada | Validar dias, turnos e intervalos antes da lógica de escala. |
| Escala-base restaurar uma remoção excepcional | Snapshot explícito por dia materializado. |
| IA produzir alterações incorretas | Estruturar saída, resolver IDs, revalidar e pedir confirmação. |
| Limite, custo ou indisponibilidade de IA | Provedor substituível e fluxos manuais independentes. |
| Dados pessoais no plano gratuito de IA | Não enviar dados reais sem avaliação/autorizações; minimização. |
| `mailto:` não abrir Outlook desejado | Testar dispositivo; oferecer cópia e abertura manual. |
| Render hibernar / Supabase pausar | Mensagens claras, retomada operacional e backups. |
| Restrições de planos gratuitos | Revisão de termos e migração se uso virar corporativo. |
| Escopo excessivo | Marcos curtos e pós-MVP separado de MVP completo. |

## 12. Próxima validação com a usuária

1. Levantar turnos e intervalos habituais, incluindo sábados.
2. Confirmar como uma ausência afeta a unidade de origem e o remanejamento.
3. Definir publicação, alteração de escala publicada e necessidade de histórico.
4. Validar protótipo da visão por unidade e formato PNG/PDF.
5. Testar o fluxo ideal de composição de e-mail no Outlook utilizado por ela.
