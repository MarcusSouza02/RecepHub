# RecepHub — Especificação Inicial de Requisitos

**Versão:** 1.1  
**Data:** 29/10/2026  
**Status:** Em refinamento com a usuária  
**Natureza:** Projeto pessoal e de portfólio, independente de organizações laboratoriais.

---

## 1. Premissas

O RecepHub será uma aplicação web responsiva e instalável (PWA), desenvolvida inicialmente para uma única usuária autenticada.

O sistema terá como finalidade centralizar informações operacionais de recepções laboratoriais, permitindo gerenciar colaboradoras, unidades, horários, escalas, férias, folgas, ausências e comunicações.

As seguintes premissas deverão orientar o desenvolvimento:

- Uma única usuária autenticada, com acesso às funcionalidades administrativas.
- Aplicação PWA com funcionamento online.
- Dados fictícios para desenvolvimento, testes e demonstrações públicas.
- Dados reais somente em ambiente privado e mediante autorização adequada.
- Cada colaboradora possuirá unidade de origem e horários habituais cadastrados.
- As escalas serão construídas a partir dessas informações habituais.
- Alterações excepcionais não modificarão automaticamente as configurações permanentes.
- A publicação de escalas deverá ocorrer somente mediante confirmação explícita.
- A inteligência artificial será opcional, substituível e não poderá realizar alterações definitivas sem confirmação.
- O envio de e-mails será realizado manualmente pela usuária, utilizando o cliente de e-mail instalado ou disponível no dispositivo.
- Os identificadores dos registros deverão permanecer estáveis.
- As datas e os horários operacionais utilizarão o fuso `America/Sao_Paulo`.
- O projeto deverá priorizar ferramentas e serviços gratuitos.

## 2. Requisitos funcionais do MVP

| ID | Requisito | Prioridade | Critério de aceite inicial |
|---|---|---|---|
| RF-01 | Efetuar login e logout com uma única conta | Alta | Rotas privadas exigem sessão válida; senha armazenada com hash seguro. |
| RF-02 | Cadastrar, editar e inativar colaboradoras | Alta | Permite cadastrar informações e preservar alocações históricas após inativação. |
| RF-03 | Cadastrar e editar unidades | Alta | Permite gerenciar unidades e vinculá-las às colaboradoras como unidade habitual. |
| RF-04 | Registrar férias, folgas, faltas e outras ausências | Alta | Registros são inseridos diretamente pela usuária e aparecem no calendário e nas consultas. |
| RF-05 | Consultar colaboradoras previstas por unidade e data | Alta | Exibe unidade, colaboradora, horário e posto, distinguindo alocação habitual e excepcional. |
| RF-06 | Criar e editar escalas diárias e semanais | Alta | Permite gerar escalas a partir das configurações habituais e realizar alterações pontuais. |
| RF-07 | Detectar conflitos de alocação e ausência | Alta | Impede publicação de horários sobrepostos ou alocações incompatíveis com ausências. |
| RF-08 | Exibir dashboard operacional | Alta | Apresenta colaboradoras escaladas, ausências, unidades e alertas relevantes. |
| RF-09 | Exportar escalas em PNG e PDF | Alta | Arquivos preservam corretamente nomes, datas, horários, unidades e postos. |
| RF-10 | Compartilhar escalas pelos recursos nativos do dispositivo | Média | Disponibiliza compartilhamento em dispositivos compatíveis e download como alternativa. |
| RF-11 | Disponibilizar instalação como PWA | Alta | Aplicação apresenta layout responsivo e pode ser instalada em dispositivos compatíveis. |
| RF-12 | Configurar necessidades mínimas de cobertura por unidade | Média | Quando configuradas, o sistema identifica cobertura inferior ao mínimo estabelecido. |
| RF-13 | Manter escalas em rascunho e confirmar publicação | Alta | Alterações não são publicadas sem confirmação explícita da usuária. |
| RF-14 | Gerar rascunhos de e-mails e comunicados utilizando IA | Alta | A usuária informa a situação, recebe um texto gerado por IA e pode revisar e editar o conteúdo. |
| RF-15 | Interpretar solicitações de alteração de escala em linguagem natural | Alta | A IA interpreta o pedido, apresenta uma proposta estruturada, o backend valida os dados e a usuária confirma a alteração. |
| RF-17 | Abrir rascunhos de e-mail no cliente de e-mail para envio manual | Alta | A usuária consegue abrir o aplicativo de e-mail com assunto e corpo preenchidos, escolher destinatários e enviar manualmente. |
| RF-20 | Manter unidades e horários habituais das colaboradoras | Alta | Configurações habituais são utilizadas como referência para as escalas e não são alteradas por exceções pontuais. |
| RF-21 | Calcular horas previstas de trabalho | Média | Calcula a duração prevista das jornadas, descontando intervalos cadastrados e considerando alterações excepcionais. |
| RF-22 | Exibir alertas de férias, folgas e ausências futuras | Alta | Dashboard apresenta eventos próximos e ausências relevantes conforme os registros cadastrados. |
| RF-23 | Disponibilizar diferentes visualizações de escala | Alta | Oferece visualização por unidade e tabela tradicional; calendário semanal poderá ser entregue progressivamente dentro do MVP. |

### 2.1. Detalhamento do RF-14 — Assistente de comunicação com IA

O aplicativo deverá disponibilizar uma interface para elaboração de comunicados utilizando inteligência artificial.

A usuária poderá informar, em linguagem natural, qual situação deseja comunicar.

Exemplo:

"Preciso informar que a colaboradora Ana começará um treinamento amanhã, das 08:00 às 17:00."

O sistema deverá:

1. Receber a solicitação da usuária.
2. Enviar o conteúdo necessário ao provedor de IA configurado.
3. Gerar uma sugestão de assunto e corpo de mensagem.
4. Apresentar o resultado em campos editáveis.
5. Permitir que a usuária revise, altere ou copie o conteúdo.
6. Disponibilizar a opção de abrir o rascunho no aplicativo de e-mail.

A funcionalidade deverá oferecer estilos de comunicação, como formal, objetivo e amigável, conforme a necessidade.

O conteúdo gerado não deverá ser enviado automaticamente.

A integração deverá respeitar os limites do plano gratuito do provedor e as regras aplicáveis ao tratamento de dados pessoais.

### 2.2. Detalhamento do RF-15 — Alterações de escala por linguagem natural

A aplicação deverá permitir que a usuária descreva alterações de escala em linguagem natural.

Exemplo:

"Hoje a Ana faltou. Coloque a Maria no lugar dela na Matriz."

O sistema deverá:

1. Interpretar a solicitação com auxílio da IA.
2. Identificar colaboradoras, unidades, datas e alterações solicitadas.
3. Consultar os registros correspondentes no banco de dados.
4. Verificar disponibilidade, ausências e possíveis conflitos de horário.
5. Identificar os impactos sobre as unidades envolvidas.
6. Apresentar uma proposta de alteração.
7. Solicitar confirmação da usuária.
8. Aplicar a alteração somente após validação e confirmação.

Quando houver informações ambíguas, o sistema deverá solicitar esclarecimentos antes de aplicar mudanças.

A IA não será responsável pela validação definitiva das regras de negócio. Essa responsabilidade permanecerá no backend.

O sistema deverá continuar permitindo alterações manuais quando a IA estiver indisponível.

### 2.3. Detalhamento do RF-17 — Integração simplificada com Outlook

A integração inicial com Outlook não utilizará Microsoft Graph API, OAuth ou acesso direto à caixa de e-mails.

O aplicativo deverá oferecer uma funcionalidade para preparar e abrir um rascunho de mensagem utilizando mecanismos de composição de e-mail disponíveis no navegador ou dispositivo.

O fluxo esperado será:

1. A usuária cria ou gera um comunicado com auxílio da IA.
2. O sistema apresenta assunto e corpo da mensagem em campos editáveis.
3. A usuária revisa o conteúdo.
4. Ao selecionar a opção de abrir no Outlook ou cliente de e-mail, o sistema utiliza o mecanismo de composição disponível.
5. A mensagem é aberta com assunto e corpo preenchidos, quando suportado pelo cliente escolhido.
6. A usuária informa manualmente os destinatários.
7. O envio é realizado diretamente pelo aplicativo de e-mail.

A aplicação deverá permitir copiar o conteúdo quando não for possível abrir automaticamente o cliente de e-mail desejado.

**Restrições:**

- O RecepHub não terá acesso à caixa de entrada.
- O sistema não enviará mensagens automaticamente.
- Não haverá armazenamento de credenciais do Outlook.
- Não haverá confirmação automática de entrega ou leitura.
- O mecanismo `mailto:` poderá abrir o cliente de e-mail padrão do dispositivo, não necessariamente o Outlook.
- O preenchimento automático dependerá das funcionalidades suportadas pelo cliente de e-mail.

Essa abordagem permitirá disponibilizar a funcionalidade gratuitamente, sem integração autenticada com os serviços da Microsoft.

### 2.4. Detalhamento do RF-20 — Configurações habituais

Cada colaboradora deverá possuir configurações habituais de trabalho.

Essas informações incluirão:

- Unidade de origem.
- Dias habituais de trabalho.
- Horários habituais de entrada e saída.
- Intervalos.
- Jornada semanal de referência, quando aplicável.

O sistema deverá utilizar essas configurações para montar a escala-base.

Quando houver alterações excepcionais, como transferências de unidade, mudanças de horário ou substituições, o ajuste deverá valer somente para as datas informadas.

As configurações habituais permanecerão preservadas, salvo quando a usuária optar por editá-las diretamente no cadastro da colaboradora.

### 2.5. Detalhamento do RF-22 — Notificações e alertas

O aplicativo deverá disponibilizar alertas internos relacionados aos registros de férias, folgas e ausências.

Exemplos:

- "Ana estará de folga amanhã."
- "Mariana iniciará as férias na próxima semana."
- "As férias de Júlia terminam em três dias."
- "Há uma colaboradora ausente na Unidade Central hoje."

Os alertas deverão ser gerados automaticamente a partir dos registros existentes.

No MVP, as notificações serão apresentadas no dashboard.

Notificações push com funcionamento fora do aplicativo serão consideradas em uma evolução posterior.

### 2.6. Detalhamento do RF-23 — Visualizações de escalas

O aplicativo deverá apresentar diferentes formas de consultar as escalas.

**Visualização por unidade — prioritária**

Exibe cada unidade com suas colaboradoras, horários de trabalho e postos.

Será a principal forma de consulta operacional.

**Tabela tradicional**

Apresenta as informações de maneira tabular, facilitando edição, conferência e exportação.

**Calendário semanal**

Exibe a distribuição das colaboradoras ao longo da semana, incluindo ausências e movimentações.

As três visualizações utilizarão a mesma fonte de dados, evitando divergências.

## 3. Requisitos pós-MVP

| ID | Requisito | Prioridade |
|---|---|---|
| RF-16 | Sugerir planejamento avançado de cobertura conforme regras de jornada e disponibilidade | Média |
| RF-18 | Integrar WhatsApp Business oficialmente, se tecnicamente viável e autorizado | Baixa |
| RF-19 | Disponibilizar histórico detalhado de versões e relatórios operacionais | Baixa |
| RF-24 | Disponibilizar notificações push no PWA | Média |
| RF-25 | Integrar Outlook via Microsoft Graph, caso exista necessidade futura e autorização | Baixa |
| RF-26 | Permitir múltiplas contas e perfis de acesso | Baixa |

O compartilhamento manual de escalas pelo WhatsApp permanece no MVP por meio do RF-10.

## 4. Requisitos não funcionais

| ID | Requisito | Verificação |
|---|---|---|
| RNF-01 | Manter custo operacional inicial igual a zero | Utilizar ferramentas e serviços gratuitos dentro das cotas disponíveis. |
| RNF-02 | Garantir interface responsiva e acessível | Testar visualização mobile/desktop, navegação por teclado, contraste e rótulos. |
| RNF-03 | Utilizar HTTPS em produção | Verificar certificados, URLs e configuração de cookies seguros. |
| RNF-04 | Armazenar senhas utilizando Argon2id ou equivalente seguro | Verificar implementação e ausência de senhas em texto puro. |
| RNF-05 | Manter credenciais e segredos fora do Git | Utilizar variáveis de ambiente e arquivos de exemplo sem valores reais. |
| RNF-06 | Garantir autenticação e autorização no backend | Testar proteção dos endpoints e acesso aos recursos. |
| RNF-07 | Implementar backups e restauração verificáveis | Testar periodicamente a exportação e recuperação de dados. |
| RNF-08 | Manter regras críticas independentes de IA | Confirmar funcionamento das operações manuais sem provedor de IA. |
| RNF-09 | Implementar testes e integração contínua | Executar pytest, lint, typecheck e pipeline no GitHub. |
| RNF-10 | Proteger dados pessoais | Minimizar coleta, separar ambientes e impedir exposição pública de informações reais. |
| RNF-11 | Considerar disponibilidade limitada dos planos gratuitos | Tratar inicialização do Render e possíveis pausas do Supabase. |
| RNF-12 | Garantir integração desacoplada de IA | Permitir substituir o provedor com alterações mínimas na lógica de negócio. |
| RNF-13 | Impedir ações definitivas executadas autonomamente pela IA | Exigir validação no backend e confirmação da usuária antes de persistir alterações. |
| RNF-14 | Garantir consistência entre escala e arquivos exportados | Validar que PNG e PDF representem os dados da escala confirmada. |
| RNF-15 | Evitar dependências pagas nas funcionalidades essenciais | Confirmar que limitações de serviços externos não impeçam o uso das operações principais. |

## 5. Histórias de usuário e critérios de aceite

### US-01 — Consultar colaboradoras por unidade

**Como** gerente de recepção,  
**quero** selecionar uma data e visualizar as colaboradoras previstas em cada unidade,  
**para** acompanhar a distribuição da equipe.

**Critérios de aceite:**

- A tela apresenta as unidades cadastradas.
- Cada unidade apresenta suas colaboradoras previstas.
- São exibidos horários e postos.
- Ausências são identificadas.
- Movimentações excepcionais são diferenciadas das alocações habituais.

### US-02 — Alterar uma escala

**Como** gerente de recepção,  
**quero** alterar a unidade, o horário ou o posto de uma colaboradora,  
**para** atender necessidades excepcionais.

**Critérios de aceite:**

- A alteração é aplicada à data informada.
- A configuração habitual permanece preservada.
- O sistema identifica possíveis conflitos.
- A alteração pode ser revisada antes da publicação.
- A exportação reflete a escala confirmada.

### US-03 — Registrar férias e folgas

**Como** gerente de recepção,  
**quero** registrar períodos de férias e folgas,  
**para** evitar escalas incompatíveis com as ausências.

**Critérios de aceite:**

- A usuária consegue cadastrar e editar ausências.
- As informações aparecem no calendário.
- O sistema identifica conflitos com escalas.
- Alocações incompatíveis não podem ser publicadas.

### US-04 — Monitorar cobertura

**Como** gerente de recepção,  
**quero** visualizar a quantidade de colaboradoras previstas em cada unidade,  
**para** identificar possíveis necessidades de cobertura.

**Critérios de aceite:**

- O sistema apresenta a distribuição por unidade.
- Quando houver requisitos mínimos cadastrados, apresenta esperado e previsto.
- Alterações excepcionais são consideradas.
- O sistema não inventa critérios de cobertura quando não existem configurações.

### US-05 — Compartilhar escalas

**Como** gerente de recepção,  
**quero** exportar escalas em PNG ou PDF,  
**para** compartilhá-las com a equipe.

**Critérios de aceite:**

- O arquivo apresenta corretamente nomes, unidades, datas e horários.
- O layout é padronizado.
- A exportação corresponde à escala publicada.
- O sistema permite baixar ou compartilhar o arquivo quando suportado.

### US-06 — Elaborar comunicados com IA

**Como** gerente de recepção,  
**quero** descrever uma situação e receber uma sugestão de comunicado,  
**para** reduzir o tempo necessário para escrever e-mails e mensagens.

**Critérios de aceite:**

- A usuária consegue informar uma solicitação em linguagem natural.
- A IA gera uma sugestão de assunto e mensagem.
- O texto pode ser revisado e editado.
- Nenhuma mensagem é enviada automaticamente.
- Falhas no provedor são tratadas sem comprometer as demais funcionalidades.

### US-07 — Abrir comunicado no Outlook

**Como** gerente de recepção,  
**quero** abrir o comunicado preparado no meu aplicativo de e-mail,  
**para** selecionar os destinatários e realizar o envio manualmente.

**Critérios de aceite:**

- A usuária consegue revisar o assunto e a mensagem.
- O sistema oferece uma opção para abrir a composição de e-mail.
- Assunto e corpo são preenchidos quando suportados pelo cliente.
- Os destinatários são definidos pela usuária.
- O aplicativo oferece a opção de copiar o conteúdo.
- O RecepHub não acessa credenciais ou mensagens da conta Outlook.

### US-08 — Solicitar alterações de escala à IA

**Como** gerente de recepção,  
**quero** descrever alterações em linguagem natural,  
**para** modificar escalas com mais rapidez.

**Critérios de aceite:**

- A IA interpreta a solicitação.
- O sistema identifica colaboradoras e unidades cadastradas.
- O backend verifica conflitos.
- Uma proposta é apresentada antes da alteração.
- A usuária confirma ou cancela a operação.
- A alteração não é aplicada automaticamente.

### US-09 — Consultar notificações

**Como** gerente de recepção,  
**quero** receber alertas sobre férias, folgas e ausências futuras,  
**para** antecipar necessidades de organização da equipe.

**Critérios de aceite:**

- O dashboard apresenta alertas de eventos próximos.
- Os alertas refletem os registros cadastrados.
- Datas são interpretadas conforme o fuso horário operacional.
- Alterações nos registros são refletidas nos alertas.

### US-10 — Consultar escala-base

**Como** gerente de recepção,  
**quero** utilizar a distribuição e os horários habituais das colaboradoras,  
**para** evitar montar escalas repetitivas do zero.

**Critérios de aceite:**

- A escala utiliza as configurações habituais cadastradas.
- Exceções são aplicadas às datas correspondentes.
- Ausências são consideradas.
- A configuração habitual não é alterada por ajustes pontuais.

## 6. Fora do MVP

As seguintes funcionalidades não serão implementadas na primeira versão:

- Controle de ponto eletrônico.
- Folha de pagamento.
- Dados de pacientes ou informações clínicas.
- Controle de produtividade individual.
- Gestão financeira do laboratório.
- Solicitação e aprovação de férias e folgas.
- Envio automático de e-mails.
- Integração autenticada com a Microsoft Graph API.
- Automação oficial do WhatsApp Business.
- Histórico avançado de versões e relatórios.
- Múltiplos usuários e perfis de acesso.
- Administração de múltiplas organizações.
- Funcionamento offline completo.
- Otimização avançada de escalas com algoritmos de restrição.
- Notificações push fora do aplicativo.

## 7. Dependências e questões pendentes

### 7.1. Jornadas e horários

Validar com a usuária:

- Horários habituais de cada colaboradora.
- Variações conforme o dia da semana.
- Intervalos.
- Jornadas aos sábados.
- Regras aplicáveis à carga horária semanal.

### 7.2. Cobertura das unidades

Identificar se existem necessidades mínimas de colaboradoras por unidade, dia ou período.

As configurações habituais poderão ser utilizadas como referência inicial, mas não deverão ser automaticamente interpretadas como quantitativos mínimos obrigatórios.

### 7.3. Dados reais

Verificar as autorizações necessárias para armazenar informações reais fora dos sistemas da organização.

O desenvolvimento e as demonstrações públicas deverão utilizar dados fictícios.

### 7.4. Serviços gratuitos

Verificar periodicamente a disponibilidade e os limites dos serviços utilizados, incluindo:

- Vercel.
- Render.
- Supabase.
- Provedor de IA gratuito.

### 7.5. Integração com Outlook

Validar o comportamento de abertura de rascunhos nos dispositivos utilizados pela usuária.

O funcionamento poderá variar entre Outlook Desktop, Outlook Web e aplicativos móveis.

### 7.6. Inteligência artificial

Definir:

- Provedor gratuito inicial.
- Modelo utilizado.
- Limites de requisições.
- Estratégia de tratamento de erros.
- Formato estruturado para propostas de alteração de escalas.
- Medidas de proteção de dados enviados ao provedor.

### 7.7. Treinamentos e outras situações

Definir como treinamentos, transferências temporárias e ausências não relacionadas a férias e folgas serão representados nas escalas.

---

## 8. Controle de alterações

| Versão | Data | Alterações |
|---|---|---|
| 1.0 | 29/10/2026 | Especificação inicial dos requisitos funcionais e não funcionais. |
| 1.1 | 29/10/2026 | Inclusão de escalas habituais, alterações excepcionais, alertas, visualizações por unidade, IA para comunicados e alterações de escala, além da abertura de rascunhos no Outlook no MVP. |

---

**Diretriz principal:** o RecepHub deverá permitir gerenciar a operação cotidiana utilizando configurações habituais como referência, automatizando atividades repetitivas sem retirar da usuária o controle sobre alterações e comunicações.