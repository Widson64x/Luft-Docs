# Configuração de EDI: ASPEN PHARMA DISTRIBUIDORA

Este documento detalha todas as configurações de EDI para o cliente **A.PHARMA DISTRIBUIDORA LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Os arquivos `CONEMB` e `DOCCOB` são gerados e enviados diretamente para o cliente, sem intermediários.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 12 horas**.
4.  O processo do `DOCCOB` é executado **a cada 5 minutos**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `edilogistica@aspenpharma.com.br`
    * `lgoncalves@br.aspenpharma.com`
    * `dcosta@br.aspenpharma.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `edilogistica@aspenpharma.com.br`
    * `lgoncalves@br.aspenpharma.com`
    * `dcosta@br.aspenpharma.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`