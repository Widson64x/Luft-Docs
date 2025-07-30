# Configuração de EDI: GUERBET RJ

Este documento detalha todas as configurações de EDI para o cliente **GUERBET PROD.RADIOLOGICOS LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONENB`    | Não    | N/A       | - |
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Apenas o arquivo `DOCCOB` é gerado e enviado.
2.  O método de envio é **E-mail Automático**.
3.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo está a lista de destinatários para o arquivo EDI. Note que o e-mail de destino é da própria Luft Logistics, indicando um processamento interno.

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*