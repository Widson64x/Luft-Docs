# Configuração de EDI: MARJAN

Este documento detalha todas as configurações de EDI para o cliente **MARJAN INDUSTRIA E COMERCIO LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | Não    | N/A       | - |
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Apenas o arquivo `CONEMB` é gerado e enviado.
2.  O método de envio é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 5 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo está a lista de destinatários para o arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `mgs.graziela@marjanfarma.com.br`
    * `rfs.rita@marjanfarma.com.br`
    * `dgn.daniel@marjanfarma.com.br`
    * `fiscal@marjanfarma.com.br`
    * `devolucoes@marjanfarma.com.br`
    * `entregas@marjanfarma.com.br`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`
    * `djair.silva@marjanfarma.com.br`