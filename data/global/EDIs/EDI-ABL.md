# Configuração de EDI: ABL

Este documento detalha todas as configurações de EDI para o cliente **ANTIBIOTICOS DO BRASIL LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim** | Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim** | Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Os arquivos `DOCCOB` e `CONEMB` são gerados e enviados diretamente para o cliente, sem intermediários.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `celula.edi@luftlogistics.com`
    * `rubens.menezes@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `contasareceber@luftlogistics.com`
    * `mike.chan@luftlogistics.com`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `contasareceber@luftlogistics.com`
    * `mike.chan@luftlogistics.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`