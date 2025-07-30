# Documentação Técnica: Módulo de Agendamento Automático

Este documento detalha a arquitetura técnica, os fluxos de dados e as principais tabelas para os processos de agendamento automático Farma e Intec, bem como o serviço de suporte.

---

## Arquitetura e Fluxo de Dados: Agendamento Farma

1.  O `JOB SP_AGENDAMENTO_IMPORTANF_FARMA_JOB` roda a cada 15 minutos, alimentado por tabelas como `Tb_CTC_ESP` e `Tb_NF_ESP`.
2.  Ele aciona a procedure `SP_AGENDAMENTO_FASE_INICIAL_FARMA`, que por sua vez, insere os dados em uma tabela espelho chamada `TB_NOTFIS_MIRROR`.
3.  Na sequência, a procedure `USP_ACERTA_MN_AGENDAMENTO_JOBFARMA` é executada, utilizando informações das tabelas `Tb_Distr_Agenda` (distribuidores exclusivos) e `Tb_Cli_Agenda` (distribuidores genéricos).
4.  O resultado é a atualização dos status de agendamento e da nota fiscal (`Mn_Agendamento` e `Mn_Status`), com o registro da operação na tabela de log `INTECLOG_LOG_SOLICITACAOAGENDAEMAILCONTROLE`.

### Diagrama
![/data/img/agendamento/img1.jpg](/data/img/agendamento/img1.jpg)

---

## Arquitetura e Fluxo de Dados: Agendamento Intec

1.  O processo Intec começa com o job `SP_AGENDAMENTO_IMPORTANF_INTEC_JOB`, que também roda a cada 15 minutos.
2.  Ele executa a procedure `SP_AGENDAMENTO_FASE_INICIAL`, que insere as informações na tabela `TB_NOTFIS_MIRROR`.
3.  A procedure `USP_ACERTA_MN_AGENDAMENTO_JOB` é chamada e, com base nos dados das tabelas de distribuidores (`Tb_Distr_Agenda` e `Tb_Cli_Agenda`), processa os agendamentos.
4.  Os status são atualizados nas colunas `Mn_Agendamento` e `Mn_Status` e o log é gravado em `INTECLOG_LOG_SOLICITACAOAGENDAEMAILCONTROLE`.

### Diagrama
![/data/img/agendamento/img2.jpg](/data/img/agendamento/img2.jpg)

---

## Arquitetura e Fluxo de Dados: Serviço de Agendamento

1.  Este processo é gerenciado por um serviço do Windows chamado `LuftServicoAgendamento`, que roda no servidor `172.16.200.82`.
2.  O serviço consulta a tabela `Tb Notfis Mirror` para montar planilhas e enviar e-mails com um link de agendamento.
3.  A interação do usuário com este link (ou o próprio serviço) pode gerar diferentes ações, como o lançamento de ocorrências B2/B3 ou 91.
4.  Essas ocorrências são registradas nas tabelas `Tb_Ocorr` e `Tb_OcorrNF`.

### Diagrama
![/data/img/agendamento/img3.jpg](/data/img/agendamento/img3.jpg)

---

## Status e Códigos Relevantes

### Status do Agendamento (`Mn_Agendamento`)
* **Descrição:** Define a etapa atual do processo de agendamento.
* **Valores Possíveis:**
    * `1`: Solicitacao Agendamto
    * `2`: Agendado
    * `3`: Solicitacao Reagenda
    * `4`: ReagendamentoCli
    * `5`: ReagendamentoLuft
    * `6`: RecusaA7
    * `7`: RecusaA9

### Status da Nota (`Mn_Status`)
* **Descrição:** Indica a condição da nota fiscal em relação à entrega.
* **Valores Possíveis:**
    * `3`: Pendente de Entrega
    * `2`: Já Entregue (tem 01, não pode agendar)

### Exemplo de Lógica em Código Fonte (SQL)
* **Quando se Aplica:** Exemplo de verificação de cliente para cobrança de tarifa.
    ```sql
    IF(SELECT COUNT(0) FROM intec..tb_Cli_Agenda CA
    WHERE CA.DS_Cgc_Cli = isnull(@pxRementente,@pxConsignatario) AND CA.FL_CobraTarifa_Cli = 0
    AND (CA.DS_Cgc_Distr = @pxDestinatario OR CA.FL_Todos_Distr = 1)) > 0
    ```