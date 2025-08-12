# Configuração de EDI: GSK - ITAPEVI

Este documento detalha todas as configurações de EDI para o cliente **GLAXOSMITHKLINE BRASIL LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | Não    | N/A       | - |
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Os arquivos `CONEMB` e `OCOREN` são gerados e enviados.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 15 minutos, todos os dias**.
4.  O processo do `OCOREN` é executado **a cada 20 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `fretes.gsk@gsk.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*