# Testes por cenário — CLARA multiagente

Cada cenário foi rodado numa sessão nova do chat (botão de reinício ao lado de **Session**),
esperando a resposta de uma mensagem antes de enviar a seguinte. O sub-agente acionado foi
conferido no painel **Logs** do editor do n8n.

| # | Mensagens | Esperado | Resposta obtida | Sub-agente (Logs) | OK? |
|---|-----------|----------|-----------------|-------------------|-----|
| 1 | "oi" | Apresenta-se como CLARA, sem ferramenta | | | |
| 2 | "Qual o horário de atendimento e o e-mail de vocês?" | INFO: seg. a sex., 8h às 17h; atendimento@nucleo-convenios.example | | | |
| 3 | "Quero saber sobre um convênio." | Nenhum: pede o número NNN/AAAA | | | |
| 4 | (sessão do 3) "É o 047/2026. Qual o objeto e o valor?" | CONVENIOS: "Pesquisa Aplicada em Tecnologias Sustentáveis" e R$ 250.000,00 | | | |
| 5 | (mesma sessão) "Quem assina pela fundação?" | CONVENIOS ou nenhum: Fernanda Lopes Azevedo, sem pedir o número | | | |
| 6 | "E o convênio 099/2026, qual o valor?" | CONVENIOS: não há registro; não cita outros convênios | | | |
| 7 | "Preciso falar com uma pessoa: meu pedido de aditivo do convênio 021/2026 está parado há um mês." e depois nome e e-mail | ATENDIMENTO: protocolo CH-…; nova linha na tabela `chamados` | | | |
| 8 | "Meu nome é Maria." e depois "Você lembra meu nome?" | Nenhum: responde Maria (memória da sessão) | | | |

## Ajustes de prompt

Preencher somente se algum cenário falhar.

| Cenário | Instrução anterior | Instrução nova | Resultado do novo teste |
|---------|--------------------|----------------|-------------------------|
| | | | |
