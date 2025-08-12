# Configuração de EDI: ASTRAZENECA

Este documento detalha todas as configurações de EDI para o cliente **ASTRAZENECA DO BRASIL LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Todos os arquivos são gerados e enviados diretamente para o cliente, sem intermediários.
2.  O método de envio para todos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.
5.  O processo do `OCOREN` é executado **a cada 8 horas, das 09:00 às 23:59, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `carla.amorim@astrazeneca.com`
    * `renato.silva1@astrazeneca.com`
    * `fabio.paiola@astrazeneca.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `carla.amorim@astrazeneca.com`
    * `renato.silva1@astrazeneca.com`
    * `fabio.paiola@astrazeneca.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `carla.amorim@astrazeneca.com`
    * `renato.silva1@astrazeneca.com`
    * `fabio.paiola@astrazeneca.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`