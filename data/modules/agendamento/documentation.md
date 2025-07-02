# Etapas do Processo de Solicitação de Agenda

O agendamento é a etapa iniciada após a emissão do CTe (Conhecimento de Transporte Eletrônico) para destinatários ou laboratórios que exigem agendamento prévio. As notas fiscais (NFs) para esses parceiros entram automaticamente em uma fila de pendências, com o status inicial de **NP (Nota Pendente)**.

O processo se divide em duas ocorrências principais:

* `B2` → **(Agendamento Distribuidores)**: A solicitação de agendamento é de responsabilidade da equipe interna "Torre de Controle", Exemplos de distribuidores que incluem são **[[Profarma]]** e **[[Raia]]**.
* `B3` → **(Agendamento Cliente)**: A solicitação é feita diretamente pelo laboratório, que é o responsável também por confirmar o agendamento. Um exemplo é a **[[GSK]]**.

## Particularidades da ocorrência B2

A execução do agendamento B2 se divide em duas particularidades, dependendo do nível de integração com o distribuidor:

### 1. Agendamento Automático (B2 Auto)

Esta modalidade é utilizada para distribuidores cujos sistemas estão integrados.

* **Como funciona**: O sistema realiza o processo de forma autônoma em horários fixos (6:00 e 15:00) para as solicitações cadastradas como automáticas.
* **Fluxo**:
    1.  Diariamente, às **6:00** ou **15:00**, o sistema processa automaticamente as notas com status **NP** (Notas Pendentes).
    2.  Um e-mail é enviado ao **distribuidor** solicitando a confirmação do agendamento.
    3.  Após o envio, o status da nota muda de **NP** para **AR** (Aguardando Retorno).
    4.  No e-mail recebido, o distribuidor clica no botão de **Confirmação**, e o agendamento é realizado.
    5.  O status da nota é atualizado para **AG** (Agendado).

* **O que acontece se o agendamento for perdido? (Reagendamento)**
    * Se ocorrer uma falha na entrega na data agendada (gerando uma ocorrência **LV** ou **RV**), o status da nota muda de **AG** para **RE (Reagendamento)**.
    * A nota com status **RE** entra novamente no fluxo automático para ser processada no próximo ciclo (6:00 ou 15:00), reiniciando o processo e voltando ao status **AR** após o novo envio de e-mail.

* **Exemplo**: A distribuidora **[[Profarma]]** utiliza este fluxo.

### 2. Agendamento Manual (B2 Manual)

É necessária quando o distribuidor não tem integração direta com o sistema.

* **Como funciona**: A solicitação é feita manualmente via portal ou e-mail, exigindo interação humana.
* **Fluxo**:
    1.  O operador acessa as notas com status **NP**.
    2.  Clica em **Contato de E-mail** e, na tela de agendamento, seleciona a agenda e envia a solicitação clicando em **Sol. Ag. (B2)**.
    3.  O status da nota muda de **NP** para **AR**.
    4.  O operador aguarda o **e-mail de confirmação** do agendamento.
    5.  Após receber a confirmação, acessa as notas com status **AR**.
    6.  Na tela de agendamento, informa o **dia e horário confirmados** e clica em **Conf. Ag. (B2)**.
    7.  O status da nota muda para **AG**.

* **O que acontece se o agendamento for perdido? (Reagendamento)**
    * Se a entrega falhar na data agendada (ocorrência **LV** ou **RV**), o status muda de **AG** para **RE (Reagendamento)**.
    * A nota com status **RE** retorna para a fila do operador. Ele deverá repetir o processo de solicitação manual (a partir do passo 2), fazendo com que o status mude de **RE** para **AR** e, posteriormente, para **AG** com a nova confirmação.

* **Exemplo**: A distribuidora **Raia** utiliza este fluxo.

## Particularidades da ocorrência B3

Esta ocorrência é acionada quando o agendamento é de responsabilidade direta do cliente (o laboratório).

* **Como funciona**: O laboratório acessa uma plataforma para consultar as notas pendentes e realiza a marcação da data e horário.
* **Fluxo**:
    1.  A nota fiscal é emitida com o status **NP** (Nota Pendente).
    2.  O **laboratório** (cliente) acessa o sistema e visualiza as NFs que precisam ser agendadas.
    3.  O cliente seleciona a data e o horário desejado.
    4.  Ao salvar a data, o status da nota é atualizado diretamente de **NP** para **AG** (Agendado), pois a solicitação e a confirmação são feitas no mesmo ato.

* **O que acontece se o agendamento for perdido? (Reagendamento)**
    * Caso ocorra uma perda de agendamento (**LV** ou **RV**), o status da nota muda de **AG** para **RE (Reagendamento)**.
    * A nota volta a ficar pendente no portal do cliente, sinalizada com o status **RE**, indicando que ele precisa realizar um novo agendamento.
    * Quando o cliente escolhe uma nova data, o status muda novamente para **AG**.

* **Exemplo**: O laboratório **[[GSK]]** utiliza este fluxo.

## Ciclo de Vida Completo no Processo de Agendamento

As notas seguem um ciclo de status que contempla tanto o caminho ideal quanto a necessidade de reagendamento.

### Fluxo Padrão

É o fluxo sem intercorrências, direto para o agendamento.


1.  **`NP` (Nota Pendente)**: Status inicial. A nota aguarda a primeira ação de agendamento.
2.  **`AR` (Aguardando Retorno)**: Status intermediário no processo B2. A solicitação foi enviada e aguarda confirmação. (O processo B3 pula esta etapa).
3.  **`AG` (Agendada)**: O agendamento foi confirmado. A nota está pronta para a programação da entrega.

### Fluxo de Reagendamento (Ciclo de Perda de Agendamento)

Este fluxo é ativado quando uma entrega agendada falha.


1.  **`AG` (Agendada)**: A nota possui uma data de entrega confirmada.
2.  **`LV` / `RV` (Perda de Agendamento)**: Ocorre uma falha na entrega. A ocorrência é registrada, e o ciclo de reagendamento é iniciado.
3.  **`RE` (Reagendamento)**: A nota entra neste estado, indicando que uma nova data precisa ser agendada com urgência.
4.  A nota **retorna ao fluxo de solicitação**:
    * **Para B2 (Auto/Manual)**: O status volta para **AR** após uma nova solicitação ser enviada.
    * **Para B3**: O cliente agenda novamente, e o status pode ir de **RE** direto para **AG**.

O ciclo se repete até que a entrega seja concluída com sucesso.

---

### Ocorrências de Agendamento

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

# 

### Siglas de Status de Agendamento

| Sigla | Descrição           | Observação                                                                      |
| :---- | :------------------ | :------------------------------------------------------------------------------ |
| `NP`  | Notas Pendente      | São todas as notas que ainda necessitam que o agendamento seja realizado.       |
| `AR`  | Aguardando Retorno  | Determina as notas que estão esperando confirmação de agenda.                   |
| `AG`  | Nota Agendada       | Determina as notas que já estão agendadas.                                      |
| `RE`  | Reagendamento       | Determina as notas que tiveram perda de agendamento (**LV** ou **RV**) e precisam ser reagendadas. |

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