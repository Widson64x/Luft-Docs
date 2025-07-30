# Configuração de EDI: ORGANON GO

Este documento detalha todas as configurações de EDI para o cliente **ORGANON FARMACEUTICA LTDA**.

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
3.  O processo do `CONEMB` e `DOCCOB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `OCOREN` é executado **a cada 1 hora, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB` e `DOCCOB`**
* **Para (`To`):**
    * `transpgo@organon.com`
* **Em Cópia (`Cc`):**
    * `mike.chan@luftlogistics.com`
    * `contasareceber@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
    * `celula.edi@luftlogistics.com`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `organon@hodieponteaerea.com`
    * `juliana.camargo@organon.com`
    * `cslbrasil@organon.com`
    * `transpgo@organon.com`
    * `organon@runtecinfo.com.br`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `leni.lima@luftlogistics.com`