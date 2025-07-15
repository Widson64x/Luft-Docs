## Visão Geral do Processo

Este documento detalha o fluxo de trabalho para o registro de coletas no sistema, desde a chegada do veículo até a emissão do romaneio e a conferência física da carga. O processo é dividido entre o registro da coleta e o recebimento de transferências, com etapas manuais e regras específicas de sistema.

## Etapa 1: Registro da Recebimento de Coleta no Sistema

O processo é iniciado no na tela de 'Recebimento Diversos' dento do módulo de Operação.

- **Início do Registro:**
    - O processo começa quando o veículo encosta na doca designada (ex: Doca 29).
    - Ao registrar a chegada no sistema, **é obrigatório retroceder o horário em 11 minutos**. O sistema não permite registrar o horário atual.

- **Preenchimento dos Dados:**
    - **Placa:** Informar a placa do veículo.
    - **Material e Modal:** A definição do tipo de material (ex: Laboratório), espécie (ex: Caixas) e modal (ex: Rodoviário). O modal aéreo é utilizado em situações específicas e urgentes, já vindo identificado nas notas.

- **Seleção de Notas:**
    - Após preencher os dados iniciais, o próximo passo é selecionar (bipar) todas as notas fiscais que farão parte daquela coleta(OBS: No caso de transferência as notas já estão manifestadas basta apenas ).
    - É recomendável fazer uma segunda contagem para garantir que nenhuma nota foi esquecida.

## Etapa 2: Processamento e Geração do Romaneio

- **Processar XML:** Após selecionar as notas, é necessário processar os arquivos XML correspondentes.

- **Geração do Romaneio:**
    - O **Romaneio** é o documento que consolida a carga. Ele é diferente de um manifesto.
    - O Romaneio contém:
        - O número das notas fiscais
        - Cliente e Destinatário
        - Peso e Volumetria (quantidade de caixas)
        - **Pallet:** Apenas para o processo de [[Transferência]] que vem com a etiqueta.

- **Finalização Manual:**
    - É preenchida uma folha de controle manual com o número do romaneio e a placa do veículo.
    - As notas fiscais e esta folha são entregues ao setor de **Emissão**, que carimba os documentos e os devolve para a o ADM de Recebimento. 

## Etapa 3: Recebimento e Conferência Física

- **Chegada do Veículo:** Quando o motorista chega ao destino, ele encosta o caminhão e apresenta as notas.

- **Conferência:**
    - O processo de conferência é **totalmente manual**, feito no papel.
    - O conferente verifica na nota fiscal a quantidade de volumes descrita (ex: 87 volumes) e conta fisicamente a carga.
    - Se houver divergência (falta ou sobra de volumes), o conferente anota o ocorrido no romaneio. Essa informação é depois lançada no sistema para tratar a ocorrência 33. ([[Ocorrências]])


## Pontos de Atenção e Dificuldades do Processo

- **Processo Manual:** A operação inteira, principalmente a conferência, é baseada em papel, o que a torna lenta e suscetível a erros.
- **Regra dos 11 Minutos:** É uma regra obrigatória do sistema e um ponto de atenção para todos os usuários que registram coletas ou transferências.
- **Troca de Motorista:** É comum que o nome do motorista no sistema não seja o mesmo que está realizando a entrega, pois ocorrem trocas de motorista durante o percurso, Isso vale para quando ocorre o processo de [[[[Transferência]]]].