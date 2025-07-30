# Configuração de EDI: HALEON - FILIAL0002

Este documento detalha todas as configurações de EDI para o cliente **HALEON BRASIL DISTRIBUIDORA LTDA** (Filial 0002).

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONENB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | Não    | N/A       | - |
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Apenas o arquivo `CONEMB` é gerado e enviado para esta filial.
2.  O método de envio é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 1 hora, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo está a lista de destinatários para o arquivo EDI. Note que o e-mail de destino é da própria Luft Logistics, indicando um processamento interno.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*