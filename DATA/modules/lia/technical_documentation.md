## Processos e Ferramentas Técnicas - Chatbot LIA

Esta seção detalha os componentes técnicos que sustentam o chatbot LIA, desde a plataforma de desenvolvimento até as integrações com os sistemas internos da Luft.

### Plataforma e Parceiro

  * **Parceiro**: **Blip**
      * Empresa especializada em plataformas de chatbot, responsável por fornecer a infraestrutura e as ferramentas para a construção e gestão da LIA.
  * **Contato Central**: Toda a comunicação com o parceiro, gestão de licenças e notificações de novos cadastros são centralizadas no e-mail: `chatbot@luft-logistica.com.br`.

### Arquitetura do Fluxo

#### 1\. Blip Builder - O Cérebro da LIA

O funcionamento da LIA é baseado em um fluxo de conversa visual projetado na ferramenta **Builder** da Blip. Ele funciona como um fluxograma onde cada "caixa" representa uma ação: enviar uma mensagem, aguardar a resposta do usuário, executar um script ou chamar uma API externa. A lógica de decisão é controlada pelas "Condições de Saída" de cada bloco.

![Visão do fluxo de conversa (Builder) na plataforma Blip](/data/img/lia/img5.png)
*O fluxograma visualiza toda a lógica de interação, desde a saudação inicial até as consultas complexas.*

#### 2\. Integração via API e Gestão de Contatos

O Builder se comunica em tempo real com os sistemas da Luft através de requisições HTTP a uma API interna.

  * **Fluxo de Validação**: Ao receber uma mensagem, o Builder aciona uma API da Luft para **validar o contato do usuário contra a base de dados do portal Luft Digital**. O retorno da API informa se o usuário está autorizado, seu perfil (padrão ou SAC) e os CNPJs associados.
  * **Gestão de Contatos**: Dentro da plataforma Blip, cada contato possui um registro com suas informações e variáveis personalizadas (`cnpjCliente`, `nomeCliente`), que são preenchidas via API e utilizadas para personalizar a conversa e as consultas.

![Tela de gestão de contato na Blip com histórico da conversa](/data/img/lia/img6.png)
*À esquerda, os dados do contato (Nome, E-mail, CNPJ) armazenados na Blip. À direita, o histórico da interação com o chatbot.*

#### 3\. Canais de Comunicação

  * **Canal Principal**: **WhatsApp**. A integração é feita através de uma conta **WABA (WhatsApp Business Account)** da Luft. A Meta (dona do WhatsApp) utiliza o ID dessa conta para monitorar o uso e garantir a conformidade com suas políticas.
  * **Potenciais Canais**: A arquitetura da Blip permite que o mesmo fluxo construído no Builder seja publicado em outros canais, como um chat em uma página web ou Telegram, se necessário no futuro.