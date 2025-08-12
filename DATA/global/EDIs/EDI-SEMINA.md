# Configuração de EDI: SEMINA

Este documento detalha todas as configurações de EDI para o cliente **SEMINA INDUSTRIA E COMÉRCIO LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | Não    | N/A       | - |
| `DOCCOB`    | Não    | N/A       | - |
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Apenas o arquivo `OCOREN` é gerado e enviado.
2.  O método de envio é **E-mail Automático**.
3.  O processo do `OCOREN` é executado **a cada 1 hora, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo está a lista de destinatários para o arquivo EDI. Note que o e-mail de destino é da própria Luft Logistics, indicando um processamento interno.

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*