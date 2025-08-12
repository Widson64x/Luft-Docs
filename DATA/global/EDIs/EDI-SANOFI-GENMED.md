# Configuração de EDI: SANOFI GENMED

Este documento detalha todas as configurações de EDI para o cliente **SANOFI MEDLEY FARMACEUTICA LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Os arquivos `CONEMB` e `DOCCOB` são gerados e enviados. Existem múltiplas configurações ativas para cada tipo de arquivo.
2.  O método de envio é **E-mail Automático**.
3.  Existem duas configurações para `CONEMB`: uma geral (a cada 1 hora) e uma para MG (a cada 5 minutos).
4.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI. Note o envolvimento de sistemas terceiros (GKO/Senior).

#### **EDI `CONEMB - SANOFI` (Geral)**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
    * `auditoria.sanofi@gko.com.br`
* **Em Cópia (`Cc`):**
    * `contasareceber@luftlogistics.com`
    * `barbara.matias@gko.com.br`
    * `fernanda.veiga@gko.com.br`
    * `sonaly.silva@gko.com.br`

#### **EDI `CONEMB - SANOFI - MG`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
    * `auditoria.sanofi@gko.com.br`
    * `yanique.moraes@senior.com.br`
* **Em Cópia (`Cc`):**
    * `contasareceber@luftlogistics.com`
    * `barbara.matias@gko.com.br`
    * `fernanda.veiga@gko.com.br`
    * `sonaly.silva@gko.com.br`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `contasareceber@luftlogistics.com`
    * `barbara.matias@gko.com.br`
    * `fernanda.veiga@gko.com.br`
    * `sonaly.silva@gko.com.br`
    * `auditoria.sanofi@gko.com.br`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`