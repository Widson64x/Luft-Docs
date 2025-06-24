# Documentação Técnica

***

## 1. Estrutura de Tabelas Relacionadas à Distribuição

1. **`dbo.tb_Distr_Agenda`**
    * Armazena informações relacionadas à agenda de distribuição por destinatário, incluindo datas, modos de envio, flags operacionais e observações.
    * Campos principais:
        * `ID_Distr_Agenda` (PK)
        * `DS_Cgc` (varchar(14))
        * `DS_Semana` (varchar(7)) - `Definido EX: '0111110' atende-se Segunda a Sexta, Sabádos e Domingos não.`
        * `DS_Obs` (varchar(200))
        * `MN_Modo_Envio_NF` (int)
        * `MN_TipoPlan` (int)
        * `FL_Ativo` (bit)
        * `FL_CobraTarifaAG` (bit)
        * `DS_Observacao` (varchar(1000))

2. **`dbo.tb_Distr_Contato`**
    * Tabela filha de `dbo.tb_Distr_Agenda`. Armazena os contatos associados a cada agenda de distribuição, incluindo informações de comunicação, preferências e dados auxiliares.
    * Campos principais:
        * `ID_Distr_Contato` (PK)
        * `ID_Distr_Agenda` (FK para `dbo.tb_Distr_Agenda`)
        * `DS_Contato` (varchar(100))
        * `DS_Cargo` (varchar(50))
        * `DS_Tel` (varchar(100))
        * `DS_Email` (varchar(100))
        * `DS_Aniver` (varchar(50))
        * `f_emite_arqcomp` (bit)
        * `FL_DistrRecebEmail` (bit)
        * `f_enviaEmailAutomatico` (bit)
        * `f_distrAgendaPerecivel` (bit)
        * `clientedistr_agendaID` (int)
        * `FL_DistrRecebWhatsApp` (bit)

    * Nessa tabela, armazenamos todos os contatos dos destinatário, e um pouco da esquemática de como trabalhar com esse destinatário

3. **`dbo.tb_NotFisMirror`**
    * Tabela de espelhamento de notas fiscais que centraliza dados relevantes ao agendamento e rastreamento de entregas.
    * Utilizada para análise de fluxo logístico, acompanhamento de status e definição de responsabilidades de agendamento.
    * Campos principais:
        * `ID_NotFisMirror` (PK)
        * `DS_Rem_Cgc` (varchar(14))
        * `NU_NFE` (numeric)
        * `DS_Serie` (varchar)
        * `DS_Dest_Cgc` (varchar)
        * `FL_CTC` (bit)
        * `DS_FilialCTC` (varchar)
        * `MN_AgendamentoID` (int)
        * `MN_Status` (int)
        * `DT_CTC` (smalldatetime)
        * `HR_CTC` (varchar)
        * `DT_Ag_Sugerida` (smalldatetime)
        * `DT_Ag_Efetivada` (smalldatetime)
        * `HR_Ag_Efetivada` (varchar)
        * `ID_Distr_Transp` (int)
        * `DS_Chave_Acesso` (varchar)
        * `DS_User_C` (varchar(50))
        * `DT_Creation` (smalldatetime)
        * `DS_User_E` (varchar(50))
        * `DT_Edition` (smalldatetime)
        * `DS_Natureza` (varchar(30))
        * `DT_Solicitacao` (smalldatetime)
        * `DT_Retorno_Sol` (smalldatetime)
        * `FL_Cli_Agenda` (bit)
        * `FL_Const_Ativo` (bit)
        * `DT_Ag_Historico` (datetime)
        * `DT_Rel_Agendamento` (datetime)
        * `Num_Pedido` (varchar(30))
        * `DT_Reag_Luft` (datetime)
        * `Qtd_Unidade` (int)
        * `Qtd_Caixas` (int)
        * `Qtd_SKUs` (int)
        * `CTC_REE` (int)
        * `ExisteVoucher` (bit)
    * Observação especial:
        * A flag `FL_Cli_Agenda` define a responsabilidade pelo agendamento:
            * Quando `FL_Cli_Agenda = 1`, significa que **o cliente é responsável por realizar o agendamento**.
            * Quando `FL_Cli_Agenda = 0`, o **time Luft realiza o agendamento diretamente**.
