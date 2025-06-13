# Coordenação de Transporte

Toda vez que for fazer uma operação relativa a um novo transporte (exceto Transferências e Distribuição), é exigido fazer a abertura de uma coordenação.

---

## Geral

Toda Coordenação é aberta para uma Filial ou uma Base.

---

## Existem vários tipos de coordenação, a saber

### Tipos de Coordenação:

- **Coleta**  
  Feita para as coletas frequentes de clientes que têm contrato. Gera uma ordem de coleta automaticamente.

- **Reversa**  
  Feita para destinatários que acumulam produtos a serem devolvidos para o remetente, onde o remetente é um cliente Luft. Gera uma ordem de coleta automaticamente.

- **Cliente retira**  
  Indicada para quando o cliente manda um veículo para retirar a mercadoria. Não gera Ordem de Coleta.

- **Transferência**  
  Exclusiva para transferências de insumos, geralmente previstas em contrato. Normalmente, o contrato prevê um número limitado de transferências sem cobrança. Gera uma ordem de coleta automaticamente.

- **Autorização retorno**  
  Para cargas que sofreram algum tipo de recusa e serão devolvidas ao cliente de origem.

- **Devolução interna**  
  Acompanha casos onde foi emitido o CTC, mas antes de sair, o cliente pede para segurar a carga. Cancela-se o CTC e gera esta coordenação para devolver a carga para o armazém.

- **Sobra**  
  Refere-se ao acompanhamento do retorno de sobras de entrega — casos em que fomos entregar, mas havia mais produtos do que o devido (visto que não se emite CTC para isso).

- **Recall**  
  Para casos de recall. A diferença para os demais é que deverá ser feita uma coleta em massa.

- **Conferência sem coleta**  
  Usada basicamente pela Roche nos casos em que é solicitado apenas fazer uma conferência do material a ser coletado.  
  O registro desta operação é feita por um aplicativo desenvolvido em coletor.  
  A cobrança é mensal, através de apuração por planilha e um CTC de cotação ao final.  
  Gera uma ordem de coleta automaticamente.

- **Conferência com coleta**  
  Usada basicamente pela Roche quando se solicita fazer conferência e coleta do material.  
  O registro é feito por aplicativo coletor.  
  Cobrança mensal via apuração por planilha e CTC de cotação ao final.  
  Gera uma ordem de coleta automaticamente.

- **Operação de insumo**  
  Acompanha a retirada de insumos, tais como mantas, loggers, etc.  
  Gera uma ordem de coleta automaticamente.

- **Dedicado**  
  Para casos onde a carga deve ser transportada por um carro exclusivo, de ponta a ponta.  
  Gera uma ordem de coleta automaticamente.

- **Pré-coordenação**  
  Permite que bases e filiais abram uma coordenação indicando uma avaria. Serve como aviso para a área de [[CRM]], evitando o tráfego de emails. A partir desta pré-coordenação, o [[CRM]] gera uma Coordenação de Autorização de Retorno.

---

## Portal de Transportes

No Portal de Transportes existe a opção das bases abrirem estas coordenações.



#### Tela com Menu de Seleção

![Tela com Menu de Seleção](/data/img/coordenação/img1.png)

---

#### Tela de Consulta (Acompanhamento)

![Tela de Consulta](/data/img/coordenação/img2.png)

---

#### Tela de Cadastro

![Tela de Cadastro](/data/img/coordenação/img3.png)


#### Funcionamento das Coordenações

As coordenações são cadastradas com a cláusula de gerar ou não uma ordem de coleta.

Geralmente são abertas pelo [[CRM]].

No caso da Coordenação tipo 5 (autorização de retorno), a Torre também pode abrir, especialmente quando após 10 dias de recusa o cliente não determina se devolve ou reentrega.

Exceto a pré-coordenação, todas as demais geram e-mails para os endereços vinculados àquela filial ou base.  
A manutenção destes e-mails é feita na tela de Cadastro de Emails de Filiais e Bases.

---

## Exemplo de E-mail de Coordenação
![Exemplo de E-mail de Coordenação](/data/img/coordenação/img4.png)

O envio dos e-mails é feito por um serviço que roda no Servidor 80 (Luft Coordenacao email).

Anexos enviados incluem uma cópia da coordenação e o PDF das notas vinculadas.

![Exemplo de Documento de Coordenação](/data/img/coordenação/img5.png)

---

### Tela de Coordenação no LuftInforma

Para incluir dados de uma coordenação, existem 7 abas com dados obrigatórios e opcionais:

1. **Dados da Coordenação** — Dados básicos.  
2. **Observação** — Caso haja alguma.  
3. **Local de Origem** — Endereço de origem da coleta. Pesquisa por endereço cadastrado ou preenchimento manual.  
4. **Local de Destino** — Endereço de destino da coleta. Pesquisa ou preenchimento manual.  
5. **Nota Fiscal** — Dados das notas fiscais da coleta. Importa XML se disponível; múltiplas notas podem ser cadastradas.  
6. **Transit Time** — Busca tabela de TT baseada no CNPJ do solicitante e motivo ‘DEV’. Se não encontrado, aplica tabela ND com prazo default (10 dias). Calcula prazo e exibe TT atual.  
7. **Log Alterações** — Histórico das ações dadas à coordenação.

![ela de Coordenação no LuftInforma](/data/img/coordenação/img6.png)

---

## Botões e Funcionalidades

- **Incluir** — Abre abas para novo cadastro.
- **Alterar** — Abre campos para alteração.
- **Gravar** — Salva o conteúdo das abas.
- **Copiar** — Clona uma coordenação para criar nova.
- **Cancelar** — Cancela alteração.
- **Excel** — Exporta dados do grid para Excel.
- **Imprimir** — Imprime dados da coordenação.
- **Filtrar** — Filtra conforme seleção nos campos superiores. Sem seleção, filtra por data de criação.
- **Sair** — Sai da tela.


## Anexos

- [Fluxo de Coordenação (PNG)](/download?token=__TOKEN_PLACEHOLDER__&download=coordenacao_fluxo.png)
- [Manual de Coordenação (DOCX)](/download?token=__TOKEN_PLACEHOLDER__&download=Coordenacao.docx)
- [Documento de Coordenação (PNG)](/download?token=__TOKEN_PLACEHOLDER__&download=Documento_Coordenacao.png)
