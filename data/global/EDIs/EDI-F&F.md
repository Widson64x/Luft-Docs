# Configuração de EDI: F&F

Este documento detalha todas as configurações de EDI para o cliente **F & F DISTRIBUIDORA DE PRODUTOS FARMACEU**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `CONENB`    | Não    | N/A       | - |
| `DOCCOB`    | **Sim**| Cliente   | Envio por E-mail.|
| `OCOREN`    | **Sim**| Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Os arquivos `DOCCOB` e `OCOREN` são gerados e enviados para o cliente.
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `DOCCOB` é executado **a cada 5 minutos, todos os dias**.
4.  O processo do `OCOREN` é executado **a cada 30 minutos, todos os dias**.

### E-mails de Envio
<div id="emails-de-envio"></div>

Abaixo estão as listas de destinatários para cada tipo de arquivo EDI.

#### **EDI `DOCCOB`**
* **Para (`To`):**
    * `megoncalves@uniaoquimica.com.br`
    * `igfpereira@uniaoquimica.com.br`
    * `edsobrinho@uniaoquimica.com.br`
    * `sleite@uniaoquimica.com.br`
    * `uniaoquimica@transpofrete.com.br`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `mquirino@uniaoquimica.com.br`
    * `lrvieira@uniaoquimica.com.br`
    * `igpereira@uniaoquimica.com.br`

#### **EDI `OCOREN`**
* **Para (`To`):**
    * `megoncalves@uniaoquimica.com.br`
    * `edsobrinho@uniaoquimica.com.br`
    * `sleite@uniaoquimica.com.br`
    * `uniaoquimica@transpofrete.com.br`
* **Em Cópia (`Cc`):**
    * `celula.edi@luftlogistics.com`
    * `mquirino@uniaoquimica.com.br`
    * `igpereira@uniaoquimica.com.br`