# Configuração de EDI: BLANVER SC

Este documento detalha todas as configurações de EDI para o cliente **BLANVER FARMOQUIMICA E FARMACEUTICA S.A.**

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Todos os arquivos são gerados e enviados.
2.  O método de envio para todos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **todos os dias, às 08:00**.
4.  O processo do `DOCCOB` é executado **a cada 1 hora, todos os dias**.
5.  O processo do `OCOREN` é executado **todos os dias, às 15:53**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI. Note que os e-mails de destino são da própria Luft Logistics, indicando um processamento interno.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*