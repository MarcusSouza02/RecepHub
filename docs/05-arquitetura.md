# RecepHub — Arquitetura Técnica

**Versão:** 1.5
**Data:** 25/11/2026
**Status:** Sprints 02–05 integradas; exportação, comunicados e assistência opcional implementados na Sprint 06, com homologação em andamento.

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
   |  HTTPS / mesma origem
   v
[Next.js — Route Handlers /api/v1: lista restrita, CSRF, cookies]
   |  BACKEND_INTERNAL_URL (somente servidor)
   v
[FastAPI — monólito modular]
   |--- auth, users
   |--- units, employees, absences
   |--- schedules (base, snapshots, conflitos, publicação)
   |--- coverage + dashboard (consultas e alertas)
   |--- communications (texto editável, exportação)
   |--- ai (interface e provedores)
   |       \--> [Gemini API opcional, conforme condições vigentes]
   \----------> [PostgreSQL]

[PWA] -- mailto:/cliente de e-mail --> [Outlook ou cliente padrão]
[PWA] -- compartilhar/exportar --> [WhatsApp ou outras opções do sistema]
```

Não existe integração autenticada com Outlook ou WhatsApp no MVP. A integração de IA ocorre **somente no backend**; a chave nunca é enviada ao navegador.

A Sprint 02 entregou autenticação, infraestrutura e dashboard vazio. A Sprint 03
acrescenta unidades, colaboradoras, horários habituais normalizados e resumo cadastral
real, mantendo modelos → repositórios → serviços → rotas e features no frontend.
O guard de servidor consulta a sessão no FastAPI antes de renderizar a página privada.
Falha técnica apresenta indisponibilidade; `401` conduz ao login. O proxy não constitui
autoridade de autenticação: o backend sempre valida token, conta ativa, revogação e validade.

Tokens opacos de 32 bytes ficam em cookie HttpOnly/SameSite=Lax/Path=/, sem Domain;
apenas SHA-256 é persistido. Cookie seguro `__Host-recephub_session` é obrigatório na
configuração de produção HTTPS. Validade absoluta de 12h e inatividade de 2h não são
prolongadas por polling: o monitor usa timer e revalida ao retomar a interface.

Login/logout exigem origem exata, cabeçalho `X-RecepHub-CSRF: 1`, JSON e corpo até 4 KiB
no proxy e na API. Login reserva uma das cinco tentativas por 15 minutos sob bloqueio
da conta em transação curta; o Argon2id é calculado depois. Sucessos e nomes incorretos
compartilham o contador PostgreSQL. Reset administrativo revoga todas as sessões.

## 4. Módulos e responsabilidades

- `auth`: login de conta única, hash Argon2id e sessão segura.
- `units`: cadastro, busca, paginação e inativação/reativação, preservando vínculos. Cobertura ainda não implementada.
- `employees`: cadastro/inativação, unidade de origem e horários semanais habituais.
- `absences`: férias, folgas, faltas e consulta por período.
- `schedules`: cálculo da escala-base, criação de snapshot diário, edição por data, verificação de conflitos, aprovação/publicação.
- `coverage`: comparação entre alocações, ausências e necessidade configurada; sem inventar valores não cadastrados.
- `dashboard`: nesta sprint, contagens reais de cadastros ativos e colaboradoras sem unidade. Alertas de férias/cobertura são futuros.
- `communications`: composição de rascunhos, abertura no cliente de e-mail, exportação de escalas.
- `ai`: tradução de pedidos para ações propostas estruturadas e auxílio de escrita; **não** faz gravações diretamente.

## 5. Fluxo RF-14 — texto de e-mail com IA

1. Frontend coleta uma descrição escrita e opções de tom.
2. Backend autentica, valida tamanho/tipo de entrada, aplica limites e verifica configuração do provedor.
3. O contrato `Provider.generate(prompt, schema)` retorna `subject` e `body` estruturados, validados pelo backend.
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

A Sprint 04 substitui a proposta diária por identidade semanal, sete estados por pessoa
e alocações efetivas. Geração/edição não alteram o habitual. expected_version e bloqueio
transacional impedem sobrescritas silenciosas. Publicação confirmada cria revisão JSONB
autocontida e imutável; edição posterior preserva todas as revisões anteriores.
Ausências/cobertura (05) reutilizam os comandos; exportação e IA (06) consomem versões
identificadas. PDF/PNG compartilham HTML/CSS confiável renderizado por Chromium, sem IA de imagem.
Outlook permanece por composição no cliente, sem envio automático ou Microsoft Graph.

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
- **ADR-008 (24/11/2026):** escala semanal materializada, estados diários, edição versionada e revisões publicadas imutáveis na Sprint 04.
- **ADR-009:** horários normalizados por pessoa/dia, sete estados explícitos, gravação semanal atômica e cálculo aritmético de minutos previstos.
- **ADR-010:** inativação preserva vínculos; novos vínculos exigem unidade ativa, com verificação transacional.

### Contratos operacionais da Sprint 03

Todas as consultas de negócio exigem sessão FastAPI. POST/PATCH/PUT exigem origem
exata, cabeçalho CSRF, JSON e limite de 4 KiB também no proxy Next.js. O proxy permite
apenas caminhos, métodos, UUIDs e parâmetros conhecidos; não recebe destinos livres.
Listagens têm busca literal, status, paginação limitada a 100 e ordenação nome/UUID.
As páginas privadas reutilizam guard, monitor de sessão e logout. A interface utiliza
componentes compartilhados e os tokens visuais observados, sem importar código Lovable.
Não há nova infraestrutura, serviço externo obrigatório ou arquitetura genérica de CRUD.

## 11. Não objetivos no MVP

Sem Graph OAuth, envio automático, leitura de caixa postal, integração oficial WhatsApp Business, notificações push, múltiplos usuários, controle de ponto, financeiro, dados clínicos, filas distribuídas ou otimização OR-Tools avançada.

## Incremento da Sprint 05

Ausências mantêm eventos por versão. Escrita bloqueia Employee antes de Absence; publicação
bloqueia Schedule, Employees e Units ordenados antes de validar ausências. Cobertura confirma
sob Schedule → Employee → Unit, revalidando disponibilidade; nenhuma escrita de ausência
adquire Schedule depois de Employee. Prévia não persiste proposta. Consultas do dashboard
usam período limitado a 31 dias e listas de 20, com total e sinalização de truncamento.
Não foi adicionada dependência de aplicação. [Plano e contratos](17-sprint-05.md).

## Incremento da Sprint 06

**ADR-004 concretizada:** Playwright Python 1.56.0 e Chromium associados na imagem Debian
Bookworm renderizam HTML/CSS confiável. PDF preserva texto; PNG usa uma página da mesma
composição. Manrope local OFL evita rede no runtime. O backend aceita apenas identificação
de revisão ou rascunho versionado, filtros e formato; não aceita HTML/URL/template livre.
Revisões usam sua fotografia imutável, e o conteúdo corrente exige seleção explícita com
marca RASCUNHO NÃO PUBLICADO em todas as páginas. A transação é liberada antes de renderizar.
Rede é bloqueada, JavaScript desativado, conteúdo escapado. Há limites de 30 páginas,
20 MiB, 30 segundos e uma geração simultânea por processo. O proxy autenticado valida
MIME, nome, tamanho e prazo do binário; respostas privadas permanecem sem cache.

**ADR-006 concretizada:** provedor substituível, desligado por padrão, com Gemini opcional
via HTTPS no host fixo e sem SDK. Habilitar exige `AI_ENABLED`, `AI_PROVIDER=gemini`, chave
`AI_API_KEY`, modelo `AI_MODEL` e `AI_ALLOW_EXTERNAL_DATA`; cada solicitação requer também
consentimento explícito. `PROPOSAL_SIGNING_KEY` privada, com ao menos 32 caracteres, é
exigida para propostas. Fake só existe por injeção nos testes. Sem configuração válida,
edição manual/exportação/comunicados continuam funcionais. Nomes/UUIDs conhecidos são
trocados por referências, mas texto livre precisa de revisão humana antes do envio.
Os [termos do provedor](https://ai.google.dev/gemini-api/terms) e eventuais cotas gratuitas
precisam ser avaliados administrativamente; não há garantia de gratuidade permanente.

Propostas permitem somente adicionar, editar ou remover períodos. Prévia não grava.
Resposta mostra pessoa/dia/unidade distinguíveis por identificador, entrada, saída,
intervalo e atividade antes/depois. Recibo HMAC vincula sessão, escala, versão, operações
normalizadas e dez minutos de validade. Confirmação explícita revalida sob bloqueios
Schedule → Employees → Units; lote inteiro grava ou desfaz. Não publica nem altera
horários habituais. Modelo não recebe SQL ou autoridade de persistência.

**ADR-007 concretizada:** preparação determinística de comunicados, editor e cópia, sem
persistência, outbox ou envio. IA de redação retorna sugestão separada e só substitui o
editor após aceite. `mailto:` não inclui destinatários; acima de 2000 caracteres na URI
codificada a interface oferece cópia integral. Cliente incompatível ou clipboard negado
também usa cópia manual. Nenhuma conexão Graph, leitura de e-mail ou disparo foi adicionada.

Contratos e evidências: [Sprint 06](19-sprint-06.md) e [relatório](20-sprint-06-relatorio-tecnico.md).
Não há migração de banco nesta sprint, ativação real de IA ou deploy como parte da entrega.
