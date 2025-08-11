# Processo CO₂

Este documento descreve o processo de mensuração de emissões de dióxido de carbono (CO2) geradas pelos fretes dos clientes. O objetivo principal é fornecer dados precisos de carbono, permitindo que os clientes utilizem os créditos gerados para suas próprias iniciativas ambientais.

## Painéis de Acompanhamento e Visualização

O acesso e a visualização dos dados do processo de CO2 são realizados através de diferentes plataformas:

* **Luft Informa**: Utilizado internamente pela equipe Luft para gestão e acompanhamento.
* **Luft Digital**: Plataforma acessível tanto por clientes quanto pela equipe Luft para consulta dos dados.
* **Via Green**: Painel específico usado internamente pela Luft, relacionado ao nosso parceiro de cálculo.

# Metodologia de Cálculo

A medição de CO₂ **não** utiliza georroteirização em tempo real. O cálculo é feito em cima do **trajeto percorrido**, que é quebrado em **pernas** (trechos) entre pontos logísticos:

- **Bases e Filiais**
- **Destinatários e Consignatários**
- **Aeroportos**

Para cada perna é registrada a **quilometragem percorrida**. A soma das pernas compõe a distância total do CTC/viagem e serve de base para o cálculo das emissões (aplicando o fator de emissão do modal/veículo cadastrado para aquele trecho).

**Exemplo**  
No fluxo abaixo, os pontos principais para o cálculo de KMs são:  
1) **Cliente → Filial Itajaí (Perna 1)** = 8,04 km  
2) **Filial SC → Matriz Itapevi (Perna 2)** = 581 km  
3) **Filial/Base → …** até o destino final, acumulando a quilometragem total.


![SC X AL](/data/img/procedimento-co2/img1.png)

**Observações práticas**
- A distância de cada perna é fixada nas ocorrências lançadas no sistema e **não depende** do trajeto real percorrido pelo veículo.

# Tela "Emissão de CO₂ — Consultar Emissões"

A tela permite **pesquisar e analisar** as emissões por CTC/viagem, filtrando por período, empresa, origem/destino, tipo de perna e mais.

![Tela Emissão de CO₂](/data/img/procedimento-co2/img2.png)

## Principais áreas e filtros
- **CTC Data / Período**: marque o checkbox e defina data inicial e final para a consulta.
- **Empresa**: filtra a companhia/holding.
- **Agrupar**: escolha campos para **agrupar** resultados (ex.: por Remetente, UF, Tipo).
- **Grupo / Radical**: filtros adicionais por grupos e por texto (radical) do campo selecionado.
- **Barra de ações**:
  - **Pesquisar**: executa a consulta.
  - **Limpar**: reseta filtros.
  - **Exportar**: exporta o resultado (planilha).
  - **Mapa**: abre o traçado/visualização do percurso.
- **Área de agrupamento**: “Arraste aqui o cabeçalho...” para criar agrupamentos dinâmicos.
- **Grade de resultados**: exibe colunas como **CTC, NF, Remetente/Origem/Destino (Nome e Local), Tipo**, **Dist. Perna** (e, quando disponível, **Dist. Total**).

## Leitura das colunas-chave
- **Tipo**: identifica o elo logístico da perna (ex.: *AEROP / BASE*, *FILIAL / BASE*, *BASE / DESTI*).
- **Dist. Perna**: distância (km) do trecho específico; some-as para checar o total do CTC.
- **Origem/Destino (Nome/Local)**: combinam **ponto logístico** e **UF/cidade** para contextualizar o trecho.
