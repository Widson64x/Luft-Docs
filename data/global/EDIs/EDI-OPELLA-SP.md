# Configuração de EDI: OPELLA SP

Este documento detalha todas as configurações de EDI para o cliente **OPELLA HEALTHCARE BRAZIL LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Os arquivos `CONEMB` e `DOCCOB` são gerados e enviados.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  Ambos os processos, `CONEMB` e `DOCCOB`, são executados **a cada 1 hora, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI. Note que a lista de cópias inclui e-mails da GKO, indicando o envolvimento de um sistema terceiro de gestão de fretes.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `contasareceber@luftlogistics.com`
    * `barbara.matias@gko.com.br`
    * `fernanda.veiga@gko.com.br`
    * `sonaly.silva@gko.com.br`
    * `yanique.moraes@senior.com.br`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `contasareceber@luftlogistics.com`
    * `barbara.matias@gko.com.br`
    * `fernanda.veiga@gko.com.br`
    * `sonaly.silva@gko.com.br`
    * `yanique.moraes@senior.com.br`