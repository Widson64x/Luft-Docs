# Configuração de EDI: PRODUTOS ROCHE - ANÁPOLIS

Este documento detalha todas as configurações de EDI para o cliente **PRODUTOS ROCHE QUIM E FARMACEUTICOS S/A**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | Não    | N/A       | - |
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Os arquivos `DOCCOB` e `OCOREN` são gerados e enviados.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `OCOREN` é executado **a cada 20 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `antonia.melo@roche.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `antonia.melo@roche.com`
    * `suzane.cotrim@roche.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`