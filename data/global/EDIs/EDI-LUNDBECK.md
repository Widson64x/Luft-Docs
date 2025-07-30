# Configuração de EDI: LUNDBECK

Este documento detalha todas as configurações de EDI para o cliente **LUNDBECK BRASIL LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONEMB`    | **Sim**| Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | Não    | N/A       | - |

### Regras de Negócio e Observações
1.  Os arquivos `CONEMB` e `DOCCOB` são gerados e enviados para o cliente.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `CONEMB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `CONEMB`**
* **Para (`To`):**
    * `ldcl@lundbeck.com`
    * `gedn@lundbeck.com`
    * `cpbauc@lundbeck.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `ldcl@lundbeck.com`
    * `gedn@lundbeck.com`
    * `cpbauc@lundbeck.com`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `contasareceber@luftlogistics.com`