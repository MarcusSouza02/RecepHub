# Sprint 03 — referência visual observada

Inspeção em 12/11/2026, em https://recephub.lovable.app/, `/unidades` e `/colaboradoras`.
Desktop 1440×1000; mobile 390×844. Navegação, DOM renderizado, estilos computados e
screenshots; nenhum envio de formulário, cópia de bundle ou exportação de código.

O host de navegação CUA estava indisponível. Playwright já existente no projeto obteve
acesso à URL pública após autorização de rede. Capturas temporárias:
`recephub-reference-{dashboard|unidades|colaboradoras}-{desktop|mobile}.png`, na pasta
temporária do sistema. O coordenador também inspecionou a captura de Unidades desktop.

## Tokens e componentes observados

| Elemento | Observação |
|---|---|
| Fundo | Creme, oklch(97.5% .018 78) |
| Card | Quase branco, oklch(99.5% .008 88) |
| Texto | Verde escuro, oklch(26% .035 150) |
| Primária | Verde, oklch(46.1% .116 153.6) |
| Sidebar | Verde profundo, oklch(25% .05 152), largura 256px |
| Borda | Bege, oklch(88% .022 80) |
| Texto secundário | oklch(50% .03 145) |
| Tipografia | Manrope corpo 16px; Sora títulos, h1 desktop 30px/600 |
| Geometria | Raio base 13,6px, cards grandes aproximadamente 18px, sombras leves |
| Header | 64px, busca/perfil e separador inferior |
| Ícones/badges | Ícones lineares, badges arredondados com ponto, avatares de iniciais |

Unidades: título/quantidade e criação; três cards por linha no desktop e uma coluna
no mobile. Colaboradoras: busca/unidade/status, tabela desktop e cards no mobile.
Margens de conteúdo 24px desktop e 16px mobile; filtros empilhados em tela estreita.
Dashboard: indicadores, grade principal 2/3–1/3, seções empilhadas no mobile.

## Adaptação aprovada e divergências

- Preservar Next.js, Tailwind e componentes existentes; incorporar apenas tokens e padrões observados.
- Usar nome da conta autenticada; não copiar nome/perfil fictício da gerente do protótipo.
- Navegação apenas Dashboard, Unidades e Colaboradoras. Omitir Escalas, Ausências, Cobertura, IA, Comunicados e Configurações sem fluxo implementado.
- Não oferecer busca global, sino ou ação IA sem comportamento real. Busca dos cadastros pertence às suas páginas.
- Não exibir cobertura mínima, pessoas trabalhando hoje, férias ou números demonstrativos.
- Cidade/descrição do contrato aprovado não serão tratadas como cadastro de endereço apenas porque o protótipo o mostra.
- Equipe habitual usa dados reais do sistema; não reproduzir avatares e nomes do exemplo publicado.
- Mobile aproveita a estrutura compacta; links e ações se restringem aos módulos desta sprint.

Não foram abertos formulários, detalhes ou editor semanal no Lovable. Não havia item
de navegação Horários na referência inspecionada; horário habitual aparece na lista
de colaboradoras. Esses fluxos serão adaptados com os padrões compartilhados, sem
afirmar fidelidade de telas não observadas. Cálculos e regras seguem o plano/documentação,
nunca os dados ou comportamentos presumidos do protótipo.
