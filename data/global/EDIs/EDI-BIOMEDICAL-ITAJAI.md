# Configuração de EDI: BIOMEDICAL - ITAJAÍ

Este documento detalha todas as configurações de EDI para o cliente **BIOMEDICAL DISTRIBUITION MERCOSUR LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONENB`    | Não    | N/A       | - |
| `DOCCOB`    | Não    | N/A       | - |
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Apenas o arquivo `OCOREN` é gerado e enviado para o cliente.
2.  O método de envio é **E-mail Automático**.
3.  O processo do `OCOREN` é executado **todos os dias, às 16:00**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo está a lista de destinatários para o arquivo EDI.

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `jonatan.perim@bomigroup.com`
    * `angelo.mileo@bomigroup.com`
    * `maria.araujo@bomigroup.com`
    * `osorio.petenao@bomigroup.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*