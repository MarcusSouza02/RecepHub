# RecepHub — Instruções para o Codex

## Contexto
RecepHub é um PWA pessoal para gestão de
recepções laboratoriais, utilizado por uma
única usuária.

## Stack
- Next.js + TypeScript
- Tailwind CSS + shadcn/ui
- FastAPI + Python
- PostgreSQL
- SQLAlchemy + Alembic
- Docker Compose

## Diretrizes
- Priorizar ferramentas gratuitas.
- Manter arquitetura simples e modular.
- Seguir os requisitos presentes em /docs.
- Utilizar dados fictícios em testes.
- Não adicionar dependências sem justificativa.
- Não modificar regras de negócio sem consultar.
- Implementar testes para regras críticas.
- Nunca colocar credenciais no Git.

## Fluxo de trabalho
Antes de implementar funcionalidades:
1. Consultar a documentação.
2. Explicar as alterações planejadas.
3. Implementar incrementalmente.
4. Executar testes.
5. Apresentar um resumo das mudanças.