# Configuração de EDI: HALEON - FILIAL0006

Este documento detalha todas as configurações de EDI para o cliente **HALEON BRASIL DISTRIBUIDORA LTDA** (Filial 0006).

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONENB`    | Não    | N/A       | - |
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Os arquivos `DOCCOB` e `OCOREN` são gerados e enviados para esta filial.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `OCOREN` é executado **a cada 1 hora, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI. Note que os e-mails de destino são da própria Luft Logistics, indicando um processamento interno.

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * *Nenhum destinatário em cópia.*