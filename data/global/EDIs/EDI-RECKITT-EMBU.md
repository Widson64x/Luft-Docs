# Configuração de EDI: RECKITT EMBU

Este documento detalha todas as configurações de EDI para o cliente **RECKITT BENCKISER HEALTH COMERCIAL LTDA.**

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Todos os arquivos (`CONEMB`, `DOCCOB`, `OCOREN`) são gerados e enviados.
2.  O método de envio para todos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` e `DOCCOB` é executado **a cada 1 minuto, todos os dias**.
4.  O processo do `OCOREN` é executado **a cada 24 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `sergio.tomaz2@reckitt.com`
    * `alexandre.ferreira@gko.com.br`
    * `auditoria.reckitt@gko.com.br`
    * `fernanda.alves2@reckitt.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`
    * `cleyton.tome@luftlogistics.com`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `sergio.tomaz2@reckitt.com`
    * `alexandre.ferreira@gko.com.br`
    * `auditoria.reckitt@gko.com.br`
    * `fernanda.alves2@reckitt.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `cleyton.tome@luftlogistics.com`