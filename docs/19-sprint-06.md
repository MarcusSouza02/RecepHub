# Sprint 06 — exportação, comunicados e assistência opcional

Início: 25/11/2026. Implementação autorizada e coordenada na branch
`feature/sprint-06-exports-communications-ai`, a partir de `dev badb47d`.
Commits sem coautor; nenhum deploy, merge em main ou alteração de credenciais.
`.env` e a alteração preexistente em `.env.example` permanecem preservados.

## Etapas e cards

| Card | Etapa | Entrega | Estado |
|---|---|---|---|
| S06-01 | 0 | Contratos e referência de documento | Definidos |
| S06-02 | 1 | Exportação protegida de revisão e rascunho | Validado localmente; CI pendente |
| S06-03 | 1 | PDF selecionável e PNG por página | Validado localmente; CI pendente |
| S06-04 | 2 | Comunicados editáveis, cópia e mailto | Validado localmente; CI pendente |
| S06-05 | 3 | Provedor substituível e estado desligado | Validado localmente; CI pendente |
| S06-06 | 4 | Prévia estruturada e confirmação transacional | Validado localmente; CI pendente |
| S06-07 | 5 | Regressão, artefatos, documentação e CI | Em andamento |

## Exportação

Geração no backend por HTML/CSS confiável, conforme ADR-004. Playwright Python 1.56.0
e o Chromium associado são dependências explícitas da imagem Debian Bookworm. O pacote
JavaScript de testes do frontend não é utilizado pelo backend. Manrope local com licença
OFL é incorporada; nenhuma fonte é baixada durante a geração.

Sob `/api/v1/schedules/{id}`: `POST /exports/preview` e `POST /exports`. Corpo JSON:
`source={kind:revision,revision_number:N}` ou `source={kind:draft,expected_version:N}`,
`format=pdf|png`, `unit_id?`, `work_date?`, `page?`. A fonte é resolvida no servidor;
nenhum HTML, URL, arquivo ou snapshot enviado pelo cliente é aceito.

Publicação é a seleção inicial quando existe revisão. Rascunho exige seleção explícita
e recebe RASCUNHO NÃO PUBLICADO, versão e identificador em todas as páginas. Revisões
usam somente sua fotografia histórica, inclusive nomes. Exportar não publica ou envia.

PDF preserva texto; PNG representa uma página do mesmo HTML/CSS em 1240×1754. Paginação
repete cabeçalhos e identificação; limite de 30 páginas, 20 MiB, 30 segundos e uma geração
simultânea por processo. Conteúdo excedente exige recorte por unidade/data. O renderer
verifica tabela e rodapé para impedir cortes. Rede bloqueada, JavaScript desabilitado e
strings escapadas. Transação de leitura liberada antes de abrir o navegador.

O proxy permite somente os caminhos e métodos explícitos, preserva MIME e filename
restritos, limita bytes recebidos e usa prazo de download adequado. Todo acesso exige
sessão; POST exige origem exata, CSRF e JSON até 4 KiB; respostas sem cache.

## Comunicados

`POST /api/v1/communications/prepare`: tipos publicação, atualização de escala, mudança
de horário/unidade, cobertura e aviso operacional. Referência opcional exige escala e
fonte juntas; publicação exige revisão. Resposta contém assunto e corpo editáveis, sem
persistência ou fila de envio. Assunto rejeita quebras de linha.

`/communications` permite preparar, editar e copiar. Mailto não contém destinatários;
o cliente de e-mail e a usuária fazem o envio. URI acima do limite conservador de 2000
caracteres oferece cópia integral, sem truncar. Falha de clipboard mantém o texto
selecionável para cópia manual. Não há Microsoft Graph ou acesso a contas de e-mail.

## Assistência opcional e propostas

IA desabilitada por padrão. O adaptador Gemini usa HTTPS no host fixo do provedor e
respostas estruturadas; não foi adicionado SDK. Modelo configurável, sem promessa de
quota ou gratuidade permanente. Provedor fake existe somente por injeção nos testes.

Habilitar exige configuração administrativa explícita: AI_ENABLED, AI_PROVIDER=gemini,
AI_API_KEY, AI_MODEL e AI_ALLOW_EXTERNAL_DATA. Cada solicitação externa também exige
consentimento na interface. Não foram criadas chaves ou modificados arquivos de ambiente.
Nomes/UUIDs conhecidos são trocados por referências locais; texto livre ainda pode conter
dados pessoais. A pessoa responsável deve revisar o texto antes de autorizar envio.

`GET /assistant/status` informa disponibilidade sem revelar segredo. `POST
/assistant/communications` sugere assunto/corpo; a interface só substitui o texto após
aceite. Erro mantém o editor manual. Propostas sob `/schedules/{id}/proposals/preview`
recebem pedido, versão e data de referência explícita. Resposta indica pronta, bloqueada
ou necessidade de esclarecimento, diferenças, impedimentos e recibo temporário.

Homônimos exigem esclarecimento ou UUID explícito. Antes/depois mostra unidade, horários,
intervalo, atividade e identificadores suficientes para distinguir registros. Somente
adição, edição e remoção de períodos são operações permitidas. Não há publicação,
alteração habitual, SQL ou autoridade de gravação concedida ao modelo.

O recibo HMAC vincula operações normalizadas à sessão, escala, versão e validade de dez
minutos. PROPOSAL_SIGNING_KEY privada de pelo menos 32 caracteres é exigida para propostas.
`POST /proposals/confirm` exige recibo e confirmação booleana explícita. O servidor
revalida tudo sob Schedule → Employees ordenadas → Units ordenadas; grava numa única
transação, incrementa versão uma vez e deixa rascunho. Falha desfaz todo o lote. Repetição
encontra versão obsoleta. Prévia não grava, e chamadas externas não seguram transação.

## Aceite e evidências

Testar documento longo, acentos, nomes máximos, seleção de texto, PNG, revisão congelada,
rascunho obsoleto, download protegido, mailto/clipboard, IA desligada/indisponível,
homônimos, recibo adulterado/expirado, sessão diferente, concorrência, ausência e rollback.
CI sem provedor externo e somente dados fictícios. Resultados efetivamente observados
serão consolidados no [relatório](20-sprint-06-relatorio-tecnico.md).
