# Configuração de EDI: MERCK - GO

Este documento detalha todas as configurações de EDI para o cliente **MERCK SHARP & DOHME FARMACEUTICA LTDA**.

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
3.  Tanto o `CONEMB` quanto o `DOCCOB` são executados **a cada 5 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI. Note que os e-mails de destino são da própria Luft Logistics, indicando um processamento interno.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `mike.chan@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`
    * `cleyton.tome@luftlogistics.com`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `mike.chan@luftlogistics.com`
    * `contasareceber@luftlogistics.com`