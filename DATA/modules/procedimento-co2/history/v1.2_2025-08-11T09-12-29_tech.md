## Processos e Ferramentas Técnicas - Cálculo de Emissões de CO2

Esta seção detalha os componentes técnicos que sustentam o processo de cálculo de CO2, desde a emissão de documentos até a comunicação com o parceiro Via Green, e o retorno dos creditos de carbono.

### Fluxo de Processamento de CO2

O fluxo de cálculo de emissões de CO2 é composto por três etapas principais, orquestradas por processos e serviços dedicados.

1.  **JOB - Emissão de CO2 (Origem e Destino)**
    * **Função**: Capturar dados de entregas a partir de diversas fontes para gerar as "pernas" de transporte e colocá-las em uma fila de processamento para o Via Green.
    * **Fontes de Informações**:
        * Ocorrências
        * Manifestos
        * Ordem de Serviço (OS) de BASE
        * Romaneio
        * AWB
    * **Processo**: O sistema utiliza esses documentos para gerar as "pernas" de transporte e realizar o cálculo entre elas. Após o cálculo, os dados são inseridos em uma fila para o Via Green.
    * **Média de Pernas**: A média de pernas varia entre 4 a 5, dependendo do TT (Tipo de Transporte).

2.  **Serviço 82 - Envio para Via Green (Alocado no 'LUFT Atualiza Imagem')**
    * **Função**: Pegar os dados da fila gerada pelo primeiro JOB e enviá-los em lotes para o parceiro Via Green. Recebe o retorno com a quantidade de CO2 calculada.
    * **Serviço de Alocação**: Este serviço está alocado no mesmo processo do 'LUFT Atualiza Imagem' que é o mesmo da Access.
    * **Limite de Processamento**: O envio de dados é limitado a 200 registros por vez.
    * **Rateio**: Após receber o retorno do Via Green, o CO2 é rateado com base no peso de cada nota fiscal.

3.  **Serviço .16 - Envio para Luft Digital (Hangfire)**
    * **Função**: Enviar os resultados do cálculo de CO2 para a plataforma da Luft Digital.
    * **Tecnologia**: O processo é executado através do Hangfire.
    * **Frequência**: O JOB, chamado 'Health Carbon Emissions', é executado a cada 90 minutos.