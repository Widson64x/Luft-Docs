# Configuração de EDI: MEAD JOHNSON

Este documento detalha todas as configurações de EDI para o cliente **MEAD JOHNSON**.

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
3.  O processo do `CONEMB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.
5.  O processo do `OCOREN` é executado **a cada 1 hora, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB` e `DOCCOB`**
* **Para (`To`):**
    * `vitor.araujo@rb.com`
    * `alexandre.dejesus2@rb.com`
    * `fernanda.alves2@reckitt.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `edirb@sistemas.msti.com.br`
    * `alexandre.dejesus2@rb.com`
    * `fernanda.alves2@reckitt.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`