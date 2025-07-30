# Entendendo o EDI (Electronic Data Interchange)

Este documento descreve o processo de **EDI (Electronic Data Interchange)** e seu funcionamento geral. O objetivo é detalhar o conceito por trás da troca eletrônica de dados entre sistemas, suas vantagens e como ele opera, preparando o terreno para futuras discussões sobre as particularidades de cada cliente.

## O que é EDI?

EDI, ou **Electronic Data Interchange**, é um padrão para a **troca eletrônica de documentos comerciais** entre empresas, de um computador para outro, em um formato padrão. Em termos mais simples, é como as empresas "conversam" eletronicamente, trocando informações importantes de negócios (como pedidos de compra, faturas, avisos de embarque) de forma padronizada e automatizada.

Imagine que, em vez de enviar e-mails, PDFs ou até mesmo documentos físicos, as informações fluam diretamente do sistema de uma empresa para o sistema da outra. Isso elimina a necessidade de entrada manual de dados, que é propensa a erros e consome muito tempo.

---

### Como Funciona o EDI?

O funcionamento do EDI envolve algumas etapas e componentes-chave:

1.  **Padronização dos Dados**: Antes de qualquer troca, as empresas precisam concordar com um **padrão de EDI**. Existem diversos padrões, como `ANSI X12` (comum na América do Norte) e `UN/EDIFACT` (internacional). Esses padrões definem a estrutura e o formato exatos dos documentos. Por exemplo, um pedido de compra (ou `850 Purchase Order` no padrão `ANSI X12`) terá campos específicos para o número do pedido, itens, quantidades, preços, etc., todos dispostos de uma forma que os computadores possam "entender".

2.  **Mapeamento de Dados**: Cada cliente tem seus próprios sistemas internos (ERPs, sistemas de vendas, etc.), que armazenam dados em formatos internos. Para que o EDI funcione, é preciso haver um **mapeamento** entre os dados internos da empresa e o formato padrão de EDI. Isso geralmente é feito por um *software* de tradução EDI.