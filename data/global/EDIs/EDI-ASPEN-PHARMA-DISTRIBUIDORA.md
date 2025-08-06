# Configuração de EDI: ASPEN PHARMA

Este documento detalha todas as configurações de EDI para o cliente **ASPEN PHARMA INDUSTRIA FARMACEUTICA LTDA**.

## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Destino?" e "Como é enviado?".

| Tipo de EDI | Mando? | Destino | Detalhes do Envio |
| :---------- | :----: | :-------: | :--------------------------------------------------- |
| `OCOREN`    | **Sim** | Cliente   | Envio por E-mail.|
| `CONEMB`    | **Sim** | Cliente   | Envio por E-mail.|
| `DOCCOB`    | **Sim** | Cliente   | Envio por E-mail.|

### Regras de Negócio e Observações
1.  Os arquivos `DOCCOB`,`OCOREN` e `CONEMB` são gerados e enviados diretamente para o cliente, sem intermediários (parceiros).
2.  O método de envio para ambos os arquivos é **E-mail Automático**.
3.  O processo do `OCOREN` é executado a cada **1 hora diariamente**.
4.  O processo do `CONEMB` é executado a cada **24 horas diariamente**.
5. O processo do `DOCCOB` é executado a cada **5 minutos diariamente**.

### E-mails de Envio
<div id="emails-de-envio"></div>

A lista de destinatários abaixo é a mesma para todos os EDIs enviados por e-mail para este cliente.

* **Para (`To`):**
    * `edilogistica@aspenpharma.com.br`
    * `lgoncalves@br.aspenpharma.com`
    * `dcosta@br.aspenpharma.com.br`
* **Em Cópia (`Cc`):**
    * `celula.ed@tflflogistics.com`