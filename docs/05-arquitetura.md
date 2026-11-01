# RecepHub — Arquitetura Técnica

**Versão:** 1.1  
**Data:** 29/10/2026  
**Status:** Proposta alinhada à ERS v1.1; IA e composição de e-mail incluídas no MVP.

## 1. Objetivo arquitetural

Entregar PWA responsivo para uma usuária, com escalas predefinidas, exceções por data, alertas de ausência e geração assistida de comunicações, preservando simplicidade, privacidade e custo inicial zero. Adotar **monólito modular**, sem microsserviços.

## 2. Stack confirmada

- **Frontend:** Next.js + TypeScript, Tailwind CSS, shadcn/ui.
- **Backend:** FastAPI + Python, Pydantic, SQLAlchemy, Alembic.
- **Banco:** PostgreSQL.
- **Desenvolvimento:** Docker Compose (`frontend`, `backend`, `postgres`).
- **PWA:** manifest, ícones, layout responsivo e HTTPS.
- **Git e CI:** GitHub, GitHub Actions, pytest, lint/typecheck, testes de UI.
- **IA:** abstração `AIProvider`, primeira opção Gemini conforme cota gratuita e política de dados; OpenAI/Ollama como alternativas futuras.
- **Hospedagem proposta:** Vercel Hobby, Render Free, Supabase Free; planos e limites devem ser rechecados no deploy.

## 3. Arquitetura lógica

```text
[PWA Next.js / navegador]
   |  HTTPS (requisições autenticadas)
   v
[FastAPI — monólito modular]
   |--- auth, users
   |--- units, employees, absences
   |--- schedules (base, snapshots, conflitos, publicação)
   |--- coverage + dashboard (consultas e alertas)
   |--- communications (texto editável, exportação)
   |--- ai (interface e provedores)
   |       \--> [Gemini API gratuita, quando habilitada]
   \----------> [PostgreSQL]

[PWA] -- mailto:/cliente de e-mail --> [Outlook ou cliente padrão]
[PWA] -- compartilhar/exportar --> [WhatsApp ou outras opções do sistema]
```

Não existe integração autenticada com Outlook ou WhatsApp no MVP. A integração de IA ocorre **somente no backend**; a chave nunca é enviada ao navegador.

## 4. Módulos e responsabilidades

- `auth`: login de conta única, hash Argon2id e sessão segura.
- `units`: cadastro/inativação de unidades e parâmetros opcionais de cobertura.
- `employees`: cadastro/inativação, unidade de origem e horários semanais habituais.
- `absences`: férias, folgas, faltas e consulta por período.
- `schedules`: cálculo da escala-base, criação de snapshot diário, edição por data, verificação de conflitos, aprovação/publicação.
- `coverage`: comparação entre alocações, ausências e necessidade configurada; sem inventar valores não cadastrados.
- `dashboard`: distribuição por unidade, próximas férias/folgas, alertas e indicadores.
- `communications`: composição de rascunhos, abertura no cliente de e-mail, exportação de escalas.
- `ai`: tradução de pedidos para ações propostas estruturadas e auxílio de escrita; **não** faz gravações diretamente.

## 5. Fluxo RF-14 — texto de e-mail com IA

1. Frontend coleta uma descrição escrita e opções de tom.
2. Backend autentica, valida tamanho/tipo de entrada, aplica limites e verifica configuração do provedor.
3. `AIProvider.generate_communication()` retorna `subject` e `body` estruturados.
4. Backend valida formato e devolve conteúdo editável ao frontend.
5. Usuária revisa e copia ou abre a composição de e-mail via `mailto:`; destinatários são escolhidos manualmente no cliente.
6. Em caso de indisponibilidade, o formulário continua utilizável manualmente.

**Privacidade:** não enviar nomes reais ou dados da empresa ao provedor sem autorização e análise das políticas aplicáveis. Evitar armazenar prompts/respostas em logs. Plano gratuito não garante tratamento equivalente a soluções empresariais.

## 6. Fluxo RF-15 — pedido de alteração de escala em linguagem natural

1. Frontend envia texto e data/contexto explícitos ao backend.
2. IA propõe JSON com operação, data, colaboradora/unidade referenciadas e parâmetros, usando schema validado.
3. Backend resolve referências a IDs reais, trata ambiguidade e verifica permissões, jornada, ausências, sobreposições e impacto de cobertura.
4. Backend devolve um **preview de mudanças** e avisos; não persiste ainda.
5. Usuária confirma a proposta; backend revalida dados atuais para evitar aplicar algo que ficou obsoleto.
6. Backend persiste mudanças apenas na escala da data selecionada. Publicação final permanece explícita e independente.

**Regra:** IA é intérprete/assistente, não mecanismo de decisão final. Edição manual funciona sem IA. Nenhum endpoint da IA recebe permissão irrestrita para criar ou publicar escalas.

## 7. Publicação, leitura e exportação

- Sem escala materializada para uma data: renderizar distribuição habitual calculada.
- Ao editar: materializar `schedule_days` + `schedule_assignments` e alterar somente a fotografia da data.
- Antes de publicar: validar o conjunto e atualizar status em uma transação.
- Tela principal: colaboradores agrupados por unidade; tabela tradicional e calendário semanal como visões do mesmo conjunto.
- Renderizar PNG/PDF deterministicamente a partir da escala aprovada, sem IA de imagem. A interface deve deixar claro quando se está visualizando um rascunho.
- Abrir e-mail: `mailto:` ou composição compatível do cliente, com alternativa de copiar texto. Não há garantia de abertura específica do Outlook caso ele não seja o padrão.

## 8. Segurança e confiabilidade mínimas

- Login único, sem autorregistro; Argon2id.
- Cookie de sessão `HttpOnly`, `Secure` e política `SameSite` adequada; considerar domínios de hospedagem diferentes, CSRF e cookies de terceiros. Preferir domínio próprio/proxy de mesma origem se a combinação de domínios inviabilizar sessão segura.
- HTTPS, CORS restrito, rate limiting em login e endpoints de IA, validação Pydantic, ORM parametrizado, limites de tamanho de entradas e saídas.
- Segredos somente no backend/ambiente seguro; `.env.example` fictício; nunca incluir chaves na imagem de frontend ou no Git.
- Dados demo fictícios; dados reais só com autorização e ambiente privado; não registrar conteúdo pessoal em observabilidade.
- Testar backup/restore; Render Free pode hibernar, Supabase Free pode pausar e exigir reativação manual; indisponibilidade deve aparecer com mensagem clara.
- Conteúdos gerados por IA são **dados não confiáveis**: validá-los e não executar instruções arbitrárias recebidas na resposta.

## 9. Qualidade e testes

- **Backend:** pytest para jornada-base, ausências, materialização diária, alterações de escala, publicação atômica, conflitos, consultas por unidade e fallback da IA.
- **IA:** mocks determinísticos em CI; nunca depender da disponibilidade do provedor nos testes.
- **Frontend:** testes de composição/revisão de e-mail, `mailto:`/cópia, visualização por unidade, confirmação de alterações, acessibilidade e responsividade.
- **E2E:** Playwright para login, edição, publicação, exportação e caminho básico do assistente.
- **CI:** lint, typecheck, build, testes e verificação de vazamento de segredos.

## 10. Decisões arquiteturais (ADRs)

- **ADR-001:** PWA em vez de aplicativos nativos.
- **ADR-002:** monólito modular em vez de microsserviços.
- **ADR-003:** PostgreSQL, SQLAlchemy e Alembic.
- **ADR-004:** renderização deterministicamente via HTML/CSS para PNG/PDF.
- **ADR-005:** conta única sem RBAC no MVP, mas autenticação robusta.
- **ADR-006:** IA desacoplada, opcional, com validação e confirmação humana.
- **ADR-007:** Outlook por abertura de composição e seleção manual de destinatários, sem Microsoft Graph no MVP.
- **ADR-008:** escala-base semanal + snapshot diário para exceções e publicação consistente.

## 11. Não objetivos no MVP

Sem Graph OAuth, envio automático, leitura de caixa postal, integração oficial WhatsApp Business, notificações push, múltiplos usuários, controle de ponto, financeiro, dados clínicos, filas distribuídas ou otimização OR-Tools avançada.
