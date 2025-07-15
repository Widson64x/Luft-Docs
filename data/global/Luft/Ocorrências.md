## Visão Geral do Processo

Este módulo visa centralizar-mos todos os tipos de ocorrÊncias possíveis no sistema caso haja alguma dúvida sobre alguma delas.


| Sigla | Descrição                         | Observação                                                          |
| :---- | :-------------------------------- | :------------------------------------------------------------------ |
| `B2`  | Agendamento via Luft              | A Luft é responsável pela solicitação de agendamento                |
| `B3`  | Agendamento via Cliente           | O Cliente é responsável pela solicitação de agendamento.            |
| `B3`  | Entrega Programada                | O Agendamento foi confirmado.                                       |
| `A7`  | Agendamento Recusado              | NF não agendada por falta de XML e ou PDF da Nota.                  |
| `A9`  | Agendamento Recusado              | Agendamento Recusado.                                               |
| `R1`  | Re-agendamento Confirmado         | O Re-agendamento foi confirmado.                                    |
| `R2`  | Re-agendamento Solicitado         | O Re-agendamento foi solicitado e aguarda confirmação.              |
| `R3`  | Re-agendamento pelo Destinatário  | O Re-agendamento foi solicitado pelo Destinatário.                  |
| `RV`  | Perda de Agendamento              | O agendamento foi perdido por uma falha **não** atribuível à Luft.  |
| `LV`  | Perda de Agendamento              | O agendamento foi perdido por uma falha atribuída à Luft.           |
| `33`  | Falta com Busca             | Quadndo a carga está com com falta de volumes.  |