# Configuração de EDI: NAOS BRASIL

Este documento detalha todas as configurações de EDI para o cliente **LABORATORIOS NAOS DO BRASIL LTDA**.

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
    * `celula.edi@luftlogistics.com`
    * `d.cesnik@bioderma.net.br`
    * `financeiro@bioderma.net.br`
    * `s.chiquete@bioderma.net.br`
    * `financeiro@bioderma.com.br`
* **Em Cópia (`Cc`):**
    * `fiscal@br.naos.com`
    * `paloma.pereira@br.naos.com`
    * `fabiana.sumiya@br.naos.com`
    * `rayssa.oliveira@br.naos.com`
    * `contasareceber@luftlogistics.com`