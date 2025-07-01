## Etapas do Processo para Lançar Agenda

O agendamento é a etapa iniciada após a emissão do CTe (Conhecimento de Transporte Eletrônico) para destinatários ou laboratórios que exigem agendamento prévio. As notas fiscais (NFs) para esses parceiros entram automaticamente em uma fila de pendências, com o status inicial de NP (Nota Pendente).

O processo se divide em duas ocorrências principais:

* `B2` → **(Agendamento Distribuidores)**: A solicitação de agendamento é de responsabilidade da equipe interna "Torre de Controle", Exemplos de distribuidores que incluem são [[Profarma]] e [[Raia]].

* `B3` → **(Agendamento Cliente)**: A solicitação é feita diretamente pelo laboratório, que é o responsável também por confirmar o agendamento. Um exemplo é a [[GSK]].

### Particularidades da ocorrência B2

A execução do agendamento B2 se divide em duas particularidades, dependendo do nível de integração com o distribuidor:

#### 1. Agendamento Automático (B2 Auto)
Esta modalidade é utilizada para distribuidores cujos sistemas estão integrados.

* **Como funciona**: O sistema realiza o processo de forma autônoma em horários fixos (6:00 e 15:00) para as solicitações cadastradas como automáticas.
* **Fluxo**:
  1. Diariamente, às **6:00** ou **15:00**, o sistema processa automaticamente as notas com status **NP** (Notas Pendentes) e que precisam do agenadamento.
  2. Um e-mail é enviado ao **distribuidor** solicitando a confirmação do agendamento.
  3. Após o envio:
     - O status da nota muda de **NP** para **AR** (Aguardando Retorno).
     - Isso indica que estamos aguardando a confirmação da agenda por parte do distribuidor.
  4. No e-mail recebido, o distribuidor tem acesso a um botão de **Confirmação**.
     - Ao clicar nesse botão, o agendamento é automaticamente realizado.
     - O status da nota é atualizado para **AG** (Agendado) no sistema.

*Exemplo*: A distribuidora **Profarma** utiliza este fluxo.

#### 2. Agendamento Manual (B2 Manual)
É necessária quando o distribuidor não tem integração direta com o sistema, exigindo interação humana para usar plataformas.

* **Como funciona**: A solicitação é feita manualmente via luft informa e portal, conforme exigência do distribuidor.
* **Fluxo**: 
  1. O operador acessa a tela de **Notas Pendentes** e seleciona as notas com status **NP**.
  2. Com as notas selecionadas, clica no botão **Contato de E-mail**, o que abre a tela de **Agendamento**.
  3. Na tela de Agendamento:
     - Seleciona-se a **agenda desejada**.
     - Informa-se o **e-mail do destinatário**.
     - Solicita-se o agendamento clicando em **Sol. Ag. (B2)**.
  4. Após a solicitação:
     - O status da nota muda de **NP** para **AR**.
     - Um e-mail é enviado ao distribuidor.
     - Uma cópia é enviada ao operador.
  5. O operador aguarda o **e-mail de confirmação** do agendamento.
  6. Após o recebimento da confirmação:
     - Acessa novamente a tela de **Notas Pendentes**, agora selecionando as notas com status **AR**.
     - Entra novamente na tela de **Agendamento**.
     - Informa o **dia e horário confirmados** no e-mail.
     - Clica no botão **Conf. Ag. (B2)** (em vez de **Sol. Ag. (B2)**).
  7. Com a confirmação:
     - O status da nota muda para **AG**.
     - O agendamento está concluído.

*Exemplo*: A distribuidora **Raia** utiliza este fluxo.

***

## Ciclo de vida no processo de agendamento

Independentemente da modalidade, as notas seguem um ciclo de status claro:

1.  **`NP` (Nota Pendente)**: Status inicial, no qual a nota fiscal aguarda a primeira ação, informando que necessita de agenda.
2.  **`AR` (Aguardando Retorno)**: O status muda para `AR` após a solicitação ser enviada (manual ou automaticamente).
3.  **`AG` (Agendada)**: Após a confirmação do distribuidor ou laboratório, o operador/sistema finaliza o processo no sistema (subindo a ocorrência 91), e o status é atualizado para `AG`.

***

## Siglas e Ocorrências de Agendamento

***

### Ocorrências de Agendamento

| Sigla | Descrição | Observação |
| :---- | :--- | :--- |
| `B2` | Agendamento via Luft | A Luft é responsável pela solicitação de agendamento |
| `B3` | Agendamento via Cliente | O Cliente é responsável pela solicitação de agendamento. |
| `B3` | Entrega Programada | O Agendamento foi confirmado. |
| `A7` | Agendamento Recusado | NF não agendada por falta de XML e ou PDF da Nota. |
| `A9` | Agendamento Recusado | Agendamento Recusado. |
| `R1` | Re-agendamento Confirmado | O Re-agendamento foi confirmado. |
| `R2` | Re-agendamento Solicitado | O Re-agendamento foi solicitado e aguarda confirmação. |
| `R3` | Re-agendamento pelo Destinatário | O Re-agendamento foi solicitado pelo Destinatário. |
| `RV` | Perda de Agendamento | O agendamento foi recusado por uma falha não atribuível à Luft. |
| `LV` | Perda de Agendamento | O agendamento foi recusado por uma falha atribuída à Luft. |

***

### Siglas de Agendamento

| Sigla | Descrição | Observação |
| :---- | :--- | :--- |
| `NP` | Notas Pendente | São todas as notas que ainda necessitam que o agendamento seja realizado. |
| `AR` | Aguardando Retorno | Determina as notas que estão esperando confirmação de agenda. |
| `AG` | Nota Agendada | Determina as notas que já estão agendadas. |
| `RE` | Re-agendamento | Determina as notas que obtiveram recusa e precisam ser reagendadas. |

***

## Telas no Sistema Luft Informa

### Tela de Cadastro de Contatos Clientes e Distribuidores

![Cadastro de Contatos Clientes e Distribuidores](data/img/agendamento/img2.png)

Nessa tela é possível definir as formas de contato tanto com o cliente quanto com os Distribuidores.

***

### Tela Cadastro de Distribuidores

![Cadastro de Distribuidores](data/img/agendamento/img1.png)

Nessa tela é possível definir todos os destinatários que são de agenda.

***

### Tela de Assinatura de E-mail

![Assinatura de Email](data/img/agendamento/img3.png)

Essa tela permite adicionar uma assinatura personalizada (telefones, etc.) ao e-mail padrão enviado para o Destinatário após a conclusão da agenda.

***

### Tela de Notas Pendentes de Agendamento

![Notas pendentes de Agendamento](data/img/agendamento/img4.png)

É uma tela de acompanhamento para ver todas as notas de agendamento e seus status. Ao selecionar uma nota e clicar no botão ‘Contato E-mail’ (canto inferior esquerdo), o operador é direcionado para a Tela de Agendamento para iniciar o processo.

***

### Tela de Agendamento

![Tela de Agendamento](data/img/agendamento/img5.png)

Nesta tela, o operador da Luft consegue realizar a agenda da nota, anexar arquivos e fazer confirmações, entre outras operações.

***

### Exemplo de Email Automático

![/data/img/agendamento/img7.png](/data/img/agendamento/img7.png)

Este email é enviado para o distribuidor, que consegue confirmar a agenda por um link, nesse link ele consegue confirmar, recusar e confirmar só que para outro dia.

***

### Exemplo de Email Manual

![/data/img/agendamento/img8.png](/data/img/agendamento/img8.png)

Este email é parecido com o anterior, porém ao invés de um link para confirmar a agenda o distribuidor retorna um e-mail informando se deseja ou não realizar a confirmação de agenda, com base nessa informação, o operador Luft realiza a a atualização, na "Tela de Agendamento".

***

### Exemplo de Email de Confimação

![/data/img/agendamento/img9.png](/data/img/agendamento/img9.png)

***

## Particularidades e Regras de Negócio
* **Alta Customização**: O processo é altamente customizado, pois cada distribuidor tem sua própria forma de solicitar o agendamento.
* **Horário de Corte**: Os agendamentos devem ser finalizados, idealmente, até as 16:00 do dia anterior.
* **Exemplo ([[RAIA]])**: Essa distribuidora exige que a solicitação de agendamento seja feita através de seu portal, um dia antes da entrega, com prazo máximo até as 09:00.
* **Voucher**: Alguns destinatários específicos só aceitam as entregas mediante a apresentação de um "voucher" de notas emitido pelo cliente.

## Botões e Funcionalidades

### Filtros de Pesquisa

A área "Dados para Pesquisa" permite ao usuário especificar múltiplos critérios para encontrar as notas desejadas.

-   **Checkboxes (Tipo)**: Permitem selecionar a origem da nota, como `INTEC` ou `FARMA`.
-   **Cliente**: Campo para selecionar um cliente específico. O valor padrão é "TODOS".
-   **Dist/Repres**: Permite filtrar por um Distribuidor ou Representante específico.
-   **Unid.**: Filtro por Unidades.
-   **DT CTe**: Filtra as notas pela data de emissão do Conhecimento de Transporte (CTe), permitindo selecionar uma data inicial (`A Partir de`).
-   **DT Sugerida**: Filtra pela data sugerida para a agendamento, também com campos de data inicial e final.
-   **Cli. Ag.**: Campo para filtrar se é o cliente que faz a própria agenda.
-   **Status**: Conjunto de caixas de seleção que representam diferentes status das notas para filtrar a busca (ex: **NP** - Nota Pendente, **AR** - Aguardando Retorno, **AG** - Agendado, **RE** - Reagendamento, **PC** - Notas Perecíveis, **SE** - Notas Sensíveis, **Rodo** - Rodoviário e **Aéreo** - Modal Aéreo.).
-   **Pesquisa**: Campo de texto livre para uma busca por um termo específico.
-   **RL**: Exportar em Excel
-   **OC**: Mostrar as Ocorrências da Nota.
-   **MN.**: Mostrar os Manifestos.
-   **VC**: Vounchers de Agendamento.

### Botões e Funcionalidades

-   **Pesq** — Realiza a busca com base nos filtros preenchidos na seção "Dados para Pesquisa" e exibe os resultados na grade.
-   **Limp** — Limpa todos os filtros aplicados e restaura os campos para seus valores padrão, permitindo uma nova busca.

### Rodapé

-   **Contato Email**: Funcionalidade para interagir com a nota, podendo realizar todas as ações de agendamento.
-   **Total NFs**: Campo que exibe a contagem total de notas fiscais retornadas pela pesquisa.
-   **NF(s) pendentes portal**: Contador específico para notas que possuem alguma pendência no portal.


## Anexos e Recursos

* [EMAIL-B2-AUTO-EXEMPLO.pdf](/download?token=__TOKEN_PLACEHOLDER__&download=B2-AUTO-EXEMPLO.pdf&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzIjoiZnJhbmNpc2NvLm1pcmFuZGEiLCJlIjoxNzUxMzA0MDI2fQ.Aw3_74HH3uZ_LlfLOXqq7bLK04FMhTH0EKJ-4663838)
* [EMAIL-B2-MANUAL-EXEMPLO.pdf](/download?token=__TOKEN_PLACEHOLDER__&download=B2-MANUAL-EXEMPLO.pdf&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzIjoiZnJhbmNpc2NvLm1pcmFuZGEiLCJlIjoxNzUxMzA0MDI2fQ.Aw3_74HH3uZ_LlfLOXqq7bLK04FMhTH0EKJ-4663838)
* [EMAIL-CONFIRMAÇÃO-DE-AGENDAMENTO.pdf](/download?token=__TOKEN_PLACEHOLDER__&download=EMAIL-CONFIRMACAO-DE-AGENDAMENTO.pdf&token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzIjoiZnJhbmNpc2NvLm1pcmFuZGEiLCJlIjoxNzUxMzA0MDI2fQ.Aw3_74HH3uZ_LlfLOXqq7bLK04FMhTH0EKJ-4663838)