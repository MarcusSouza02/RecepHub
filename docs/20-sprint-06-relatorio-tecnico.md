# Sprint 06 — relatório técnico

Atualizado em 25/11/2026. Implementação, testes automatizados e revisão independente concluídos localmente.
Conferência visual concluída; publicação e CI remota em finalização.

## Base e coordenação

Branch própria a partir de `dev badb47d`, Sprints 04–05 integradas e validadas. Três
subagentes implementaram exportação, comunicados/interface e IA/propostas. O coordenador
centralizou contratos, dependências, imagem, proxy, navegação, testes e documentação.
Revisão independente por gpt-6-astra xhigh, sem escrita nos arquivos.

## Inventário

| Arquivos/grupo | Finalidade |
|---|---|
| `backend/app/schemas/exports.py` | Fonte explícita, filtros, formato e página |
| `backend/app/services/exports.py` | Fotografia copiada e transação liberada antes de renderizar |
| `backend/app/services/export_renderer.py` | HTML/CSS escapado, fonte local, paginação e Chromium offline |
| `backend/app/api/v1/exports.py` | Prévia JSON e download binário autenticado |
| `backend/app/assets/fonts/` | Manrope e licença OFL para runtime independente do frontend |
| `backend/app/schemas/communications.py`, `services/communications.py`, `api/v1/communications.py` | Preparação determinística de assunto e corpo, sem envio |
| `backend/app/services/ai/` | Contrato de provedor, desligado, fake por DI e Gemini opcional |
| `backend/app/schemas/proposals.py`, `services/proposals.py`, `api/v1/assistant.py` | Validação, recibo HMAC, prévia e confirmação atômica |
| `backend/app/core/config.py`, `compose.yaml` | Configuração opcional, sem alterar `.env` ou `.env.example` |
| `backend/pyproject.toml`, `requirements.lock`, `infra/backend.Dockerfile` | Playwright Python e dependências transitivas fixadas; Chromium na imagem |
| `frontend/src/services/downloads.ts`, proxy existente | Download com MIME/filename restritos, limite de bytes e prazo próprio |
| `frontend/src/features/exports/export-panel.tsx` | Seleção de fonte e recorte histórico, prévia e download |
| `frontend/src/features/communications/`, `app/communications/page.tsx` | Editor, cópia, mailto e aceite de sugestão |
| `frontend/src/features/assistant/assistant-panel.tsx` | Estado desligado, pedido, diferenças completas e confirmação |
| Navegação e `schedules-client.tsx` | Entradas dos novos fluxos e preservação da revisão somente leitura |
| `backend/tests/test_exports.py`, `test_communications.py`, `test_proposals.py` | Regras, segurança e integração |
| `backend/tests/test_proposal_safety.py` | Jornada/pausa, lote atômico, ausência concorrente e repetição concorrente de confirmação |
| `frontend/tests/e2e/exports.spec.ts`, `communications.spec.ts`, `assistant.spec.ts` | Cenários de download, comunicação e limites da assistência |
| Workflow e `tests/e2e_admin.py` | Renderer real na CI e fixtures limitadas ao novo banco de navegador |

## Decisões e correções da revisão

HTML/CSS continua sendo a fonte visual comum do PDF e PNG. PDF não é uma captura raster.
Fonte local não consulta rede. O conteúdo deve ser equivalente para a mesma fotografia e
opções; metadados binários internos do PDF não são prometidos como bytes idênticos.

A revisão identificou diferenças incompletas da IA: pausas e atividade passaram a ser
exibidas, PATCH exige todos os campos explícitos e nulls são preservados no recibo.
Referências estáveis distinguem homônimos. Resolução de nomes considera pessoas e unidades
em uma passagem conjunta, por correspondência completa e maior comprimento. O recorte da
exportação usa a revisão selecionada no próprio formulário, independentemente da escala
visível. A regressão posterior à revisão foi aprovada. O detalhe da unidade passou a
exibir sua referência selecionável, permitindo distinguir unidades homônimas fora da escala.

## Evidências e pendências

- Primeira bateria completa: 294 testes backend aprovados, incluindo Chromium real e
  PostgreSQL descartável. Um warning conhecido do TestClient permaneceu reportado.
- Após correções da revisão: 308 testes backend aprovados, com o mesmo warning conhecido.
  Inclui duas conexões reais para ausência concorrente e repetição de confirmação.
- Dez testes focados do renderer aprovados após os ajustes finais de paginação e PNG.
- Regressão final integrada: **309 testes aprovados**, com Chromium real e PostgreSQL
  descartável; um warning conhecido do TestClient, sem filtros para ocultá-lo.
- Ruff e formatação aprovados (106 arquivos); ESLint, TypeScript e build aprovados.
- Bateria completa de navegador: **62 aprovados em uma execução**, desktop e mobile.
  Inclui download real PDF/PNG, comunicados e regressão das sprints anteriores. Cenários
  de IA da interface usam respostas simuladas; o backend usa provedor fake por injeção.
- Inspeção dos artefatos confirmou acentos, texto selecionável, identificador em todas
  as páginas e nomes publicados preservados após alteração cadastral. PDF publicado e
  rascunho tinham duas páginas cada; todas foram renderizadas e inspecionadas visualmente.
  PNG da última página: **1240×1754**. Ligaturas foram desativadas para cópia literal;
  seleção da folha na origem eliminou arredondamento na captura de páginas posteriores.
- Paginação considera comprimentos máximos e quebras de linha; sete linhas com nomes
  máximos ocuparam quatro páginas sem cortes. Cem linhas habituais ocuparam nove páginas.
- pypdf e PyMuPDF foram ferramentas temporárias de inspeção, sem dependência da aplicação.
- Revisão independente final: nenhum bloqueador P0/P1/P2 identificado após correções.
- Seis capturas da interface inspecionadas: comunicados, escala corrente e revisão
  histórica em desktop 1440×1000 e mobile 390×844. Sem overflow ou erros de página;
  foco visível, acentos corretos e histórico sem controles de edição/assistente.
  Link mailto validado sem abrir nem enviar mensagem. Capturas temporárias, não versionadas.
- Publicação e CI remota pendentes nesta atualização.

Ambiente isolado: bancos `recephub_sprint06_test` e `recephub_sprint06_browser_test` no
PostgreSQL temporário existente; API exclusiva `recephub-sprint06-api-test` em loopback
3384. Imagem `recephub-sprint06-backend:latest`; dados fictícios. Desenvolvimento intacto.

## Dependências e limitações

Playwright Python 1.56.0, pyee 13.0.1 e greenlet 3.5.6 foram adicionados ao lock.
Chromium build 1194 e bibliotecas do sistema ampliam a imagem e o primeiro build.
IA não é requisito para exportação, edição da escala ou comunicados. A oferta gratuita
do provedor pode usar conteúdo para melhoria de produtos; ativação exige avaliação dos
[termos](https://ai.google.dev/gemini-api/terms) e das condições vigentes. Não houve envio
externo nos testes, ativação real de IA ou provisionamento de chave.

## Reprodução manual

Reconstrua as imagens e confira `alembic current/check`; a Sprint 06 não cria tabelas.
Em `/schedules`, selecione uma revisão e exporte PDF/PNG; selecione rascunho explicitamente
e confira sua marca. Prepare comunicado da versão, edite/copie e abra mailto sem enviar.
Com IA desligada, os fluxos manuais devem continuar funcionais. Configuração opcional e
limites constam no [plano](19-sprint-06.md). Não executar reset/downgrade no desenvolvimento.
