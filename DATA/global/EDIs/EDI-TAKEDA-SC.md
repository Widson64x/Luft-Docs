# Configuração de EDI: TAKEDA - SC

Este documento detalha todas as configurações de EDI para o cliente **TAKEDA DISTRIBUIDORA LTDA** (unidade de Santa Catarina).

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Todos os arquivos (`CONEMB`, `DOCCOB`, `OCOREN`) são gerados e enviados.
2.  Existem duas configurações para cada tipo de arquivo: uma **FARMA** e uma **INTEC**, com agendamentos distintos.
3.  O método de envio para todos os arquivos é **E-mail Automático**.

### Detalhes e E-mails de Envio
<div id="emails-de-envio"></div>

O destinatário para todas as configurações abaixo é:
* **Para (`To`):** `celula.edi@luftlogistics.com`
* **Em Cópia (`Cc`):** *Nenhum destinatário em cópia.*

#### **EDI `CONEMB`**
* **CONEMB (FARMA):** Executado a cada 8 horas.
* **CONEMB (INTEC):** Executado a cada 8 horas.

#### **EDI `DOCCOB`**
* **DOCCOB (FARMA):** Executado a cada 12 horas.
* **DOCCOB (INTEC):** Executado a cada 12 horas.

#### **EDI `OCOREN`**
* **OCOREN (FARMA):** Executado a cada 1 hora, 24h por dia.
* **OCOREN (INTEC):** Executado a cada 1 hora, das 08:00 às 19:59.