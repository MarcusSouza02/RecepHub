# RecepHub — Regras de Negócio
**Versão:** 1.1 | **Status:** regras operacionais da Sprint 03 aprovadas; regras de escalas e cobertura ainda propostas

## 1. Conceitos
- **Unidade de origem:** referência cadastral de colaboradora.
- **Alocação:** atribuição para uma unidade, data, intervalo de horário e posto naquele dia.
- **Posto:** texto/identificador na alocação (por exemplo: Guichê 1, Triagem, Unimed, Treinamento); não exige tabela `workstations`.
- **Ausência:** férias, folga ou outro impedimento durante período determinado.
- **Cobertura:** número de pessoas simultaneamente disponíveis em uma unidade por faixa horária, comparado a requisito configurado.

## 2. Regras propostas
| ID | Regra | Status |
|---|---|---|
| RN-01 | Uma colaboradora pode trabalhar em unidade diferente da origem. | Confirmada conceitualmente |
| RN-02 | A mesma colaboradora não pode ter alocações em horários sobrepostos. | Proposta |
| RN-03 | Alocação incompatível com férias/folga ativa bloqueia publicação. | Proposta |
| RN-04 | Postos mudam livremente por data; título do posto pertence à alocação. | Confirmada conceitualmente |
| RN-05 | Um mesmo guichê não deve ter duas colaboradoras simultâneas na mesma unidade, se o posto representa posição exclusiva. | A validar |
| RN-06 | Necessidade mínima de pessoal varia por unidade, data e faixa horária. | A validar |
| RN-07 | Horários e pausas são explícitos. A Sprint 03 calcula minutos previstos por aritmética; isso não valida contratos, legislação ou horas trabalhadas. | Aprovada na Sprint 03 |
| RN-08 | Escalas são rascunho até a ação de publicar. | Proposta |
| RN-09 | Inativar colaboradora ou unidade preserva os registros. Vínculos existentes com unidade inativa permanecem sinalizados; novos vínculos exigem unidade ativa. | Aprovada na Sprint 03 |
| RN-10 | IA apenas propõe texto/edições, sujeitos a validação e confirmação. | Confirmada arquiteturalmente |
| RN-11 | Dados públicos de demonstração são fictícios; dados reais não vão ao Git. | Confirmada |
| RN-12 | Fuso de exibição: America/Sao_Paulo; auditoria em UTC. | Proposta |

## 3. Algoritmo básico de validação
Para cada alocação: (a) verificar existência e status da colaboradora; (b) checar início/fim e intervalo; (c) buscar alocações com interseção temporal; (d) buscar ausências incompatíveis; (e) verificar ocupação simultânea do posto exclusivo, se configurado; (f) somar cobertura por janela de tempo; (g) apresentar erros impeditivos e avisos antes de publicar.

## 4. Exemplos de cenário de teste
1. Funcionária A na Unidade Central, 06:00–12:00; tentar escalar 10:00–16:00 na Unidade Norte → conflito.
2. Funcionária B de férias entre 02 e 10/11; alocar em 05/11 → bloqueio.
3. Funcionária C muda do Guichê 1 na segunda para Triagem na terça → permitido.
4. Unidade X requer 4 pessoas de 08:00–12:00 e só 3 estão previstas → alerta de cobertura, não geração fictícia de uma quarta pessoa.
5. Nome/horário alterado em rascunho → arquivo exportado corresponde à versão escolhida/publicada.

## 5. Pontos para entrevista
- Lista e características das unidades e dias de funcionamento.
- Horário de abertura e fechamento; turnos; intervalos de almoço; jornada por pessoa.
- Quantos postos exclusivos existem e se há posto dinâmico especial.
- Mínimos de cobertura em dias úteis, sábados e horários de pico.
- Como são tratadas férias, folgas, falta, treinamento, banco de horas e substituição.
- Situações excepcionais nas quais a gerente precisaria de um aviso em vez de bloqueio.
- Como a escala é aprovada, alterada e comunicada hoje.

> Nota: exemplos de jornadas, quantidade mínima de pessoas, unidades e postos não são regras definitivas do produto até confirmação com a usuária.

## 6. Regras aprovadas para cadastros e horários — Sprint 03

- Unidade habitual é opcional; nomes iguais são permitidos, diferenciados por UUID.
- Cada colaboradora possui sete dias explícitos, de segunda a domingo. Novos cadastros começam com `pending`; dia pendente não representa folga.
- `working` admite um período e um intervalo opcional no mesmo dia. Horários incompletos podem ser salvos; contradições conhecidas são rejeitadas. Não há jornada presumida no sábado ou domingo.
- `non_working` representa dia explicitamente sem trabalho, sem horários. `pending` também não carrega horários.
- O subtotal soma apenas dias completos; o total semanal só existe quando os sete dias estiverem definidos. Intervalo incompleto impede o cálculo daquele dia.
- A substituição semanal exige sete dias únicos e ocorre em uma única transação.
- Inativar uma unidade não desvincula colaboradoras. É permitido manter o vínculo já existente ou removê-lo; uma nova atribuição requer unidade ativa.
- Indicadores desta sprint contam unidades ativas, colaboradoras ativas e colaboradoras ativas sem unidade habitual. Não representam pessoas trabalhando hoje ou cobertura por horário.
