## 1. Problema

A gestão cotidiana de recepções laboratoriais envolve o acompanhamento de colaboradoras, unidades, horários de trabalho, escalas, férias, folgas, treinamentos e movimentações temporárias.

Atualmente, essas informações podem estar distribuídas entre planilhas, documentos, mensagens e outros meios de comunicação, dificultando a consulta centralizada e a atualização das escalas.

Embora as colaboradoras possuam unidades e horários de trabalho habitualmente definidos, situações excepcionais, como faltas, férias, folgas e treinamentos, exigem alterações pontuais na distribuição das equipes.

A realização manual dessas alterações pode gerar retrabalho, conflitos de horários, dificuldades na identificação de substituições e inconsistências no compartilhamento das escalas.

## 2. Objetivo

Desenvolver uma aplicação web responsiva e instalável (Progressive Web App — PWA), destinada inicialmente a uma única usuária, com o objetivo de centralizar e facilitar a gestão operacional de recepções laboratoriais.

O sistema deverá permitir:

- Cadastrar e consultar colaboradoras e unidades.
- Definir unidades e horários habituais de trabalho.
- Gerar escalas com base nas configurações predefinidas.
- Realizar alterações pontuais sem modificar os horários e as unidades habituais.
- Registrar e visualizar férias, folgas, faltas e outras ausências.
- Identificar necessidades de cobertura decorrentes de ausências ou alterações.
- Exibir notificações sobre eventos importantes e futuros.
- Consultar a distribuição das colaboradoras por unidade.
- Exportar e compartilhar escalas em formatos padronizados.
- Utilizar inteligência artificial opcional para auxiliar na organização de escalas e na elaboração de comunicações, em marcos posteriores ao núcleo operacional e dentro do MVP completo.

O principal objetivo é reduzir atividades repetitivas, melhorar a visualização das informações e facilitar a tomada de decisões operacionais.

## 3. Usuária e partes interessadas

### 3.1. Usuária principal

Uma gerente de recepção laboratorial, responsável por organizar e acompanhar a distribuição das colaboradoras entre unidades.

Será a única usuária autenticada na versão inicial do sistema, com permissão para cadastrar, consultar, editar e excluir informações.

### 3.2. Desenvolvedor

Responsável pela análise de requisitos, arquitetura, implementação, testes, documentação, manutenção e evolução do projeto.

### 3.3. Colaboradoras

Funcionárias cadastradas no sistema, associadas a unidades e horários habituais de trabalho.

Suas informações serão utilizadas para organização das escalas, registro de ausências e planejamento de cobertura.

As colaboradoras não terão acesso individual ao aplicativo no MVP.

### 3.4. Organização empregadora

A organização na qual a usuária trabalha não será patrocinadora, proprietária ou responsável pelo desenvolvimento do software.

O RecepHub será desenvolvido como projeto independente. A utilização de informações reais da organização e de suas colaboradoras deverá respeitar a legislação aplicável, as políticas internas e as autorizações necessárias.

## 4. Valor esperado

O RecepHub deverá proporcionar os seguintes benefícios:

- **Centralização:** reunir informações de colaboradoras, unidades, horários, férias e folgas em um único ambiente.
- **Agilidade:** reduzir o tempo necessário para consultar e modificar escalas.
- **Padronização:** utilizar unidades e horários habituais como referência para a criação de escalas.
- **Flexibilidade:** permitir alterações excepcionais sem comprometer as configurações permanentes.
- **Visibilidade:** apresentar rapidamente quais colaboradoras estão previstas em cada unidade.
- **Prevenção:** identificar ausências e possíveis necessidades de cobertura antes que impactem a operação.
- **Organização:** disponibilizar alertas sobre férias, folgas e outros eventos futuros.
- **Comunicação:** facilitar a exportação e o compartilhamento de escalas e comunicados.
- **Aprendizado:** proporcionar experiência prática em Engenharia de Software, desenvolvimento web, banco de dados, infraestrutura, segurança e integração com inteligência artificial.

## 5. Princípios e restrições

### 5.1. Custo inicial zero

O desenvolvimento deverá priorizar ferramentas gratuitas, open source e serviços com planos gratuitos.

A operação inicial não deverá depender de assinaturas pagas.

Serviços externos poderão apresentar limitações de uso, disponibilidade e desempenho, que deverão ser consideradas durante a implementação.

### 5.2. Simplicidade arquitetural

O sistema utilizará uma arquitetura de monólito modular, evitando complexidade desnecessária.

Não serão implementados inicialmente microsserviços, múltiplas organizações ou gerenciamento avançado de permissões.

A estrutura deverá, entretanto, permitir futuras evoluções sem exigir uma reescrita completa da aplicação.

### 5.3. Usuária única

O MVP possuirá uma única conta autenticada.

A senha será armazenada por meio de hash criptográfico seguro, e a autenticação deverá utilizar mecanismos adequados de gerenciamento de sessão.

### 5.4. Privacidade e proteção de dados

O código-fonte e os exemplos publicados no GitHub deverão utilizar exclusivamente dados fictícios.

Informações reais de colaboradoras e unidades, quando autorizadas, serão armazenadas em uma instância privada, protegida por autenticação e controles de acesso.

Nenhuma informação interna ou pessoal deverá ser incluída em repositórios públicos.

### 5.5. Inteligência artificial opcional

A integração com inteligência artificial será implementada de maneira desacoplada, permitindo substituir o provedor utilizado.

Inicialmente, serão priorizadas alternativas gratuitas, como o Gemini API, observadas suas limitações e políticas de tratamento de dados.

A IA poderá interpretar solicitações, sugerir alterações e elaborar comunicações, mas não poderá publicar escalas, modificar registros definitivos ou enviar mensagens sem confirmação da usuária.

### 5.6. Renderização determinística de escalas

As escalas serão representadas por dados estruturados e renderizadas pelo sistema utilizando componentes de interface.

A geração de arquivos PNG e PDF deverá preservar corretamente os nomes, horários, unidades e postos de trabalho.

A imagem final não dependerá de geração por inteligência artificial.

### 5.7. Escalas baseadas em configurações habituais

Cada colaboradora possuirá uma unidade de origem e uma configuração habitual de horários.

O sistema utilizará essas informações como referência para criar e exibir as escalas, permitindo alterações para datas específicas.

Uma alteração excepcional não deverá modificar automaticamente a configuração habitual da colaboradora.

## 6. Escopo do MVP

### 6.1. Autenticação

- Login de uma única usuária.
- Senha armazenada com hash seguro.
- Gerenciamento de sessão.
- Proteção das funcionalidades contra acesso não autenticado.

### 6.2. Gestão de unidades

- Cadastrar unidades.
- Editar informações das unidades.
- Consultar unidades cadastradas.
- Desativar unidades sem excluir seus registros históricos.
- Visualizar as colaboradoras habitualmente vinculadas a cada unidade.

### 6.3. Gestão de colaboradoras

- Cadastrar colaboradoras.
- Editar informações cadastrais.
- Definir unidade de origem.
- Definir horários habituais de trabalho.
- Registrar dias habituais de trabalho e intervalos.
- Consultar a distribuição das colaboradoras.
- Desativar colaboradoras sem apagar o histórico de escalas.

### 6.4. Gestão de férias, folgas e ausências

As férias, folgas e demais ausências serão cadastradas diretamente pela usuária.

Não haverá fluxo de solicitação ou aprovação.

O sistema deverá permitir:

- Registrar férias com data inicial e final.
- Registrar folgas para datas específicas.
- Registrar faltas e outras ausências.
- Editar e excluir registros de ausências.
- Consultar ausências por colaboradora, unidade e período.
- Visualizar ausências em calendário.
- Identificar conflitos entre ausências e escalas previstas.

### 6.5. Notificações e alertas

O MVP deverá disponibilizar alertas internos no dashboard, incluindo:

- Colaboradoras de folga no dia seguinte.
- Férias com início previsto nos próximos dias.
- Férias próximas do encerramento.
- Ausências previstas para o dia atual.
- Possíveis necessidades de cobertura decorrentes das ausências.

Os alertas deverão ser calculados a partir dos dados cadastrados, sem necessidade de inteligência artificial.

**Evolução futura:** notificações push no PWA, permitindo avisar a usuária mesmo quando o aplicativo não estiver aberto, dependendo das permissões do dispositivo e de um mecanismo de agendamento.

### 6.6. Gestão de escalas

O sistema deverá utilizar as configurações habituais das colaboradoras como referência para a criação das escalas.

Serão disponibilizadas funcionalidades para:

- Consultar escalas por dia e por semana.
- Gerar uma escala-base a partir das alocações e horários habituais.
- Alterar a unidade de uma colaboradora em uma data específica.
- Alterar horários de entrada, saída e intervalo em situações excepcionais.
- Definir postos de atendimento, como guichês, triagem e Unimed.
- Identificar conflitos de alocação.
- Identificar colaboradoras escaladas durante períodos de ausência.
- Calcular horas previstas de trabalho por dia e semana.
- Editar e confirmar alterações antes de atualizar a escala.

A carga horária calculada representará as horas previstas na escala, não necessariamente as horas efetivamente trabalhadas.

### 6.7. Visualização de escalas

O sistema contará com três formatos de visualização.

**Visualização por unidade — principal**

Apresentará as unidades e suas respectivas colaboradoras, com horários e postos de atendimento.

Será a principal visualização operacional do sistema, priorizada no dashboard.

**Tabela tradicional**

Apresentará as escalas em formato tabular, facilitando consultas, edições e exportações.

**Calendário semanal**

Permitirá visualizar a distribuição das colaboradoras e os eventos de ausência ao longo da semana.

Essa visualização poderá ser implementada progressivamente.

### 6.8. Dashboard operacional

O dashboard deverá apresentar informações importantes para a rotina da usuária, incluindo:

- Quantidade de colaboradoras ativas.
- Quantidade de unidades cadastradas.
- Distribuição de colaboradoras por unidade.
- Ausências previstas para o dia.
- Próximas férias e folgas.
- Alertas de possíveis conflitos ou necessidades de cobertura.
- Acesso rápido às escalas e aos cadastros.

### 6.9. Planejamento básico de cobertura

O sistema deverá identificar alterações na distribuição habitual das colaboradoras.

Quando uma colaboradora for removida de uma unidade ou transferida temporariamente, o aplicativo deverá permitir verificar possíveis impactos na cobertura da unidade de origem e da unidade de destino.

Inicialmente, o planejamento de cobertura poderá utilizar a comparação entre a distribuição habitual e a distribuição prevista na escala.

Regras mais avançadas sobre quantitativos mínimos de atendimento por unidade, dia ou faixa de horário serão definidas após validação com a usuária.

### 6.10. Exportação e compartilhamento

- Exportar escalas em PNG.
- Exportar escalas em PDF.
- Gerar documentos com identidade visual própria.
- Permitir compartilhamento manual pelo celular.
- Facilitar o envio das escalas por WhatsApp ou e-mail utilizando os recursos disponíveis no dispositivo.

### 6.11. Progressive Web App

O sistema deverá:

- Ser responsivo para computadores e celulares.
- Permitir instalação na tela inicial de dispositivos compatíveis.
- Possuir ícone e identidade visual próprios.
- Oferecer navegação adaptada para telas menores.
- Utilizar conexão HTTPS em produção.

O funcionamento offline completo não será requisito inicial.

## 7. Evolução incremental e funcionalidades após o MVP

As seções 7.1 e 7.2 integram o MVP completo, conforme a ERS v1.1, e serão entregues após o
núcleo operacional. As seções 7.3 a 7.6 descrevem evoluções pós-MVP.

### 7.1. Assistente de inteligência artificial

Implementar um assistente capaz de compreender solicitações em linguagem natural.

Exemplo:

"Hoje a Ana faltou. Coloque a Maria no lugar dela na Matriz."

O sistema deverá interpretar a solicitação, consultar os dados disponíveis, verificar conflitos e apresentar uma proposta de alteração para confirmação.

### 7.2. Geração de comunicados

Utilizar inteligência artificial para:

- Redigir e-mails profissionais.
- Reformular mensagens.
- Elaborar comunicados para WhatsApp.
- Preparar avisos sobre mudanças de horários e escalas.
- Adaptar a linguagem ao contexto solicitado.

### 7.3. Planejamento avançado de cobertura

- Identificar unidades com cobertura inferior à necessidade definida.
- Sugerir substituições de colaboradoras.
- Considerar férias, folgas, faltas e horários disponíveis.
- Identificar os impactos de transferências temporárias.
- Apresentar alternativas para reorganização de escalas.

### 7.4. Integrações externas

- Integração com Outlook por meio da Microsoft Graph API, quando autorizada.
- Integração com serviços oficiais de mensagens, quando tecnicamente viável e compatível com o orçamento.
- Notificações push para eventos futuros.

### 7.5. Histórico e relatórios

- Histórico de alterações de escalas.
- Relatórios de distribuição de colaboradoras.
- Indicadores de ausências.
- Relatórios de horas previstas.
- Comparação entre escalas habituais e excepcionais.

### 7.6. Expansão de usuários

Caso exista demanda futura, poderão ser implementados:

- Múltiplas contas.
- Perfis e permissões.
- Acesso individual para colaboradoras.
- Administração por diferentes gerentes.
- Separação de informações entre organizações.

Essas funcionalidades não fazem parte do escopo inicial.

## 8. Critérios iniciais de sucesso

O MVP será considerado funcional quando:

1. A usuária conseguir acessar o aplicativo pelo computador e pelo celular.
2. For possível cadastrar unidades e colaboradoras com suas respectivas configurações habituais.
3. O sistema conseguir apresentar a distribuição prevista das colaboradoras por unidade.
4. As escalas puderem ser geradas utilizando os horários e as unidades habituais.
5. Uma alteração pontual puder ser realizada sem modificar os dados habituais.
6. O sistema identificar conflitos básicos de horários e ausências.
7. A usuária conseguir registrar férias e folgas e visualizá-las no calendário.
8. O dashboard apresentar alertas sobre ausências e eventos próximos.
9. As escalas puderem ser exportadas corretamente em PNG e PDF.
10. O aplicativo puder ser instalado como PWA em dispositivos compatíveis.
11. Os dados privados estiverem protegidos por autenticação.
12. O repositório público não apresentar dados reais ou credenciais.

Os critérios serão detalhados posteriormente em cenários de teste e critérios de aceite.

## 9. Questões abertas e decisões de negócio

### 9.1. Distribuição de colaboradoras por unidade

**Status: Definido parcialmente**

Cada unidade possui colaboradoras habitualmente designadas.

Essa distribuição deverá ser cadastrada como configuração padrão, permitindo alterações excepcionais em datas específicas.

As alterações temporárias não deverão modificar automaticamente a unidade de origem.

**Pendente:** definir se existem quantidades mínimas de cobertura por unidade ou por horário e como serão estabelecidas.

### 9.2. Férias e folgas

**Status: Definido**

As férias e folgas serão cadastradas diretamente pela usuária.

O aplicativo será responsável por armazenar, organizar, exibir e sinalizar os eventos.

Não haverá solicitações ou aprovações.

Serão disponibilizados alertas internos no MVP e estudada a implementação futura de notificações push.

### 9.3. Horários e jornadas

**Status: Definido parcialmente**

Cada colaboradora possui horários habituais predefinidos.

O aplicativo deverá utilizar esses horários como referência e permitir modificações pontuais.

Também deverá realizar o cálculo das horas previstas de trabalho.

**Pendente:** identificar como os horários variam conforme o dia da semana, especialmente aos sábados, e quais regras de jornada e intervalo devem ser utilizadas.

### 9.4. Utilização de informações reais

**Status: Pendente de autorização**

O aplicativo será preparado para cadastrar os nomes reais das unidades e das colaboradoras em uma instância privada.

O uso efetivo dessas informações deverá respeitar as políticas da organização e as autorizações necessárias.

O desenvolvimento, os testes públicos e o portfólio utilizarão dados fictícios.

### 9.5. Formato visual das escalas

**Status: Definido**

Serão consideradas três visualizações:

1. Organização por unidade.
2. Tabela tradicional.
3. Calendário semanal.

A visualização por unidade terá prioridade por facilitar a consulta operacional.

### 9.6. Escalas habituais e exceções

**Status: Definido**

O sistema terá como referência a distribuição habitual das colaboradoras e seus horários predefinidos.

A usuária poderá registrar exceções, como faltas, transferências, mudanças de horário e substituições temporárias.

Alterações excepcionais serão aplicadas às datas correspondentes, preservando os dados habituais.

### 9.7. Inteligência artificial

**Status: Incluído no MVP completo; implementação posterior ao núcleo operacional**

O sistema utilizará uma integração desacoplada de provedor, priorizando soluções gratuitas.

A inteligência artificial poderá auxiliar na interpretação de solicitações e na preparação de alterações, mas qualquer modificação definitiva exigirá confirmação da usuária.

---

## 10. Tecnologias definidas

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js + TypeScript |
| UI/UX | Tailwind CSS + shadcn/ui |
| Backend | FastAPI + Python |
| Banco de dados | PostgreSQL |
| ORM | SQLAlchemy |
| Migrações | Alembic |
| Ambiente local | Docker Compose |
| Aplicativo | Progressive Web App (PWA) |
| Autenticação | Conta única e senha com hash seguro |
| Versionamento | Git + GitHub |
| Inteligência artificial | Integração substituível |
| Hospedagem frontend | Vercel |
| Hospedagem backend | Render |
| Banco gerenciado | Supabase |

As escolhas de hospedagem poderão ser revistas conforme a disponibilidade e as condições dos planos gratuitos.

---

## 11. Diretrizes de evolução

O desenvolvimento será incremental, priorizando funcionalidades de maior utilidade operacional.

A arquitetura deverá manter separação entre interface, regras de negócio, persistência de dados e integrações externas.

O sistema não deverá depender da inteligência artificial para realizar suas operações essenciais.

As regras de negócio deverão ser documentadas e validadas antes da implementação dos módulos correspondentes.

Alterações relevantes de escopo deverão ser registradas na documentação, preservando o histórico das decisões.

**Princípio central do RecepHub:** simplificar a gestão cotidiana de recepções laboratoriais utilizando informações habituais como referência, permitindo administrar exceções com agilidade, segurança e clareza.
