# Documentação Técnica

---

## 1. Estrutura de Tabelas Relacionadas à Coordenação

1. **`Intec..tb_Coordenacao`**  
   - Armazena todas as coordenações oriundas das Filiais e Bases.  
   - Campos principais:  
     - `coordenacao_id` (PK)  
     - `filial_id` (FK para `Intec..tb_Filial`)  
     - `tipo_id` (FK para `Intec..tb_CoordenacaoTipo`)  
     - `data_solicitacao` (datetime)  
     - `gera_ordem_coleta` (bit)  
     - `status_id` (FK para `Intec..tb_CoordenacaoStatus`)  
     - `observacao` (varchar(max))

2. **`Intec..tb_CoordenacaoTipo`**  
   - Define os tipos de coordenação disponíveis.  
   - Campos principais:  
     - `tipo_id` (PK)  
     - `descricao` (varchar(100))  
     - `flag_gera_ordem_coleta` (bit)

3. **`Intec..tb_CoordenacaoStatus`**  
   - Controla os possíveis status de cada coordenação e permissões por perfil.  
   - Campos principais:  
     - `status_id` (PK)  
     - `descricao` (varchar(50))  
     - `perfil_permite` (varchar(50))

4. **`Intec..tb_CoordenacaoMotivo`**  
   - Lista motivos válidos para cada tipo de coordenação.  
   - Campos principais:  
     - `motivo_id` (PK)  
     - `tipo_id` (FK)  
     - `descricao` (varchar(200))

5. **`Intec..tb_CoordenacaoAcao`**  
   - Histórico completo de ações realizadas em cada coordenação, registrando data, usuário e descrição.  
   - Campos principais:  
     - `acao_id` (PK)  
     - `coordenacao_id` (FK)  
     - `data_hora` (datetime)  
     - `usuario` (varchar(50))  
     - `status_anterior_id` (FK para `tb_CoordenacaoStatus`)  
     - `status_posterior_id` (FK para `tb_CoordenacaoStatus`)  
     - `motivo_id` (FK)

6. **`Intec..tb_CoordenacaoEmails`**  
   - Tabela que vincula as Filiais/Bases aos endereços de e-mail que recebem notificações automáticas.  
   - Campos principais:  
     - `email_id` (PK)  
     - `filial_id` (FK)  
     - `email_destino` (varchar(100))

7. **`Intec..tb_CoordenacaoStatusPermissoes`** *(opcional, caso exista separadamente)*  
   - Define quais perfis de usuário podem alterar quais status.  
   - Campos principais:  
     - `status_id` (FK)  
     - `perfil_id` (FK)

---

## 2. Jobs e Processos Agendados

1. **Job `Atualiza_Coordenacao_luftinforma`**  
   - **Periodicidade:** Executa de hora em hora.  
   - **Responsabilidades:**  
     1. Atualiza CTCs com ocorrência “b5” (coleta realizada) e “b1” (retorno) para o status “Coleta Realizada”.  
     2. Verifica Ordens de Serviço de coleta baixadas para tipos de Coordenação 1, 3 e 4, atualizando status conforme retorno do sistema de roteirização.

2. **Serviço “LuftInforma Coordenação Takeda”**  
   - **Periodicidade:** Intervalo configurável, tipicamente a cada 15 minutos.  
   - **Fluxo:**  
     - Lê arquivos texto no diretório do Servidor 82.  
     - Importa dados para as tabelas `Inteclog..tbImportaCoordenacao` e `Inteclog..tbImportaCoordenacaoItens`.  
     - Trata duplicidade de coordenações.  
     - Gera automaticamente registros em `Intec..tb_Coordenacao` e associadas Ordens de Coleta.  
     - Envia notificações conforme parâmetros.

3. **Serviço “Luft Coordenacao email”**  
   - **Periodicidade:** Executa continuamente para monitorar novas coordenações que demandem envio de e-mail.  
   - **Responsabilidades:**  
     - Recupera destinatários de `Intec..tb_CoordenacaoEmails`.  
     - Anexa PDF gerado da coordenação e PDFs de notas fiscais.  
     - Dispara e-mail via SMTP configurado no Servidor 80.

---

## 3. Regras de Negócio e Validações

1. **Flag de Geração de Ordem de Coleta**  
   - Conforme tipo de coordenação, o campo `flag_gera_ordem_coleta` em `tb_CoordenacaoTipo` define se será gerada uma Ordem de Coleta.  
   - A aplicação deve validar, ao gravar, se o tipo selecionado permite ordem; caso negativo, não criar registro em `tb_OrdemColeta`.

2. **Verificação de Motivação por Tipo**  
   - Ao alterar status, a aplicação deve consultar `tb_CoordenacaoMotivo` para listar apenas motivos compatíveis com o tipo de coordenação.  
   - Impede o usuário de atribuir motivos inadequados ao tipo de operação.

3. **Permissões de Ação por Perfil**  
   - Usuários possuem perfis que determinam quais ações de status podem executar.  
   - Antes de mudar status, a aplicação verifica `tb_CoordenacaoStatusPermissoes` (ou a lógica interna de perfis) para validar a permissão.

4. **Cálculo de Transit Time (TT)**  
   - Na aba “Transit Time”, o sistema busca Tabela de TT com base em:  
     - CNPJ do solicitante.  
     - Motivo (campos `tipo` e `motivo`).  
   - Se não encontrar correspondência, utiliza Tabela ND (não diferenciada) e aplica prazo padrão de 10 dias.  
   - O cálculo de prazo deve considerar dias úteis (excluindo sábados, domingos e feriados), segundo calendário interno.

5. **Histórico de Alterações (Log)**  
   - Cada ação de usuário que alterar dados críticos (status, motivo, endereços, datas) gera um registro em `tb_CoordenacaoAcao`.  
   - Mantém rastreabilidade completa: usuário, data/hora, status anterior e posterior, motivo e eventuais observações.

---

## 4. Estrutura de Geração de Relatórios e Impressão

1. **Geração de PDF de Coordenação**  
   - O serviço de geração de PDF consome dados de:  
     - `Intec..tb_Coordenacao` (dados principais).  
     - `Intec..tb_CoordenacaoAcao` (log resumido).  
     - `Inteclog..tbImportaCoordenacaoItens` (quando originada via importação Takeda).  
     - Dados de notas fiscais: fonte externa (integração com repositório de XML).  
   - **Layout:**  
     - Cabeçalho com logotipo institucional Luft.  
     - Seções com datas, remetente, destinatário e tabelas de itens.  
     - Rodapé com QR Code de rastreamento.

2. **Exportação para Excel (Grid)**  
   - Ao clicar em “Excel” na tela de consulta, a aplicação executa uma query parametrizada que seleciona colunas como:  
     - `coordenacao_id`, `filial`, `tipo`, `status`, `data_criacao`, `data_prevista`, `origem`, `destino`, `gerou_ordem_coleta`.  
   - Gera um arquivo `.xlsx` via biblioteca interna (ex.: EPPlus ou OpenXML).  
   - Oferece download imediato ao usuário.

3. **Impressão Direta**  
   - Chamadas via JavaScript (ou .NET Print API) para renderizar PDF em janela de visualização, permitindo impressão local.

---

## 5. Integrações Externas e Serviços Dependentes

1. **Integração com CRM**  
   - **Pré‐coordenação:**  
     - Quando o usuário informa avaria no Portal, gera‐se registro em `tb_PreCoordenacao` (estrutura interna).  
     - O CRM consome esta tabela para, posteriormente, gerar uma “Coordenação de Autorização de Retorno”.

2. **Sistema de Roteirização / OS de Coleta**  
   - Os tipos 1 (Coleta), 3 (Cliente Retira) e 4 (Transferência) se comunicam com sistema de roteirização externa (via webservice/REST API).  
   - Recebem status de OS (Ordem de Serviço) para atualização periódica via `Atualiza_Coordenacao_luftinforma`.

3. **Armazenamento de XMLs de Nota Fiscal**  
   - Quando o usuário importa XML na aba “Nota Fiscal”, o sistema:  
     - Deserializa o arquivo XML.  
     - Extrai campos relevantes (número da nota, data, valor, CNPJ emitente/destinatário, itens).  
     - Persiste registros em `Inteclog..tbNFEntrada` (tabela central de Notas Fiscais).  
     - Armazena o XML físico em repositório interno, referenciando caminho em campo `caminho_xml`.

4. **Envio de E-mails via SMTP**  
   - Configuração no Servidor 80 aponta para servidor SMTP corporativo (porta 25 ou 587).  
   - Serviço utiliza bibliotecas .NET `MailMessage`/`SmtpClient` (ou JavaMail, conforme linguagem).  
   - Template de e-mail montado com tecnologia Razor (ou equivalente), unindo dados do banco de `tb_Coordenacao` e anexos PDF.

---

## 6. Gestão de Parâmetros e Cadastros Auxiliares

1. **Cadastro de Filial/Base**  
   - Tabela `Intec..tb_Filial` contém:  
     - `filial_id` (PK)  
     - `nome_filial` (varchar(100))  
     - `cnpj_filial` (varchar(18))  
     - `endereco_padrao` (varchar(200))  
   - Define quais usuários terão visibilidade e autorização.

2. **Cadastro de Endereços (Local de Origem/Destino)**  
   - Tabela `Intec..tb_Endereco` armazena:  
     - `endereco_id` (PK)  
     - `logradouro`, `numero`, `bairro`, `cidade`, `estado`, `cep`.  
   - No formulário de coordenação, pesquisa‐se nesta tabela ou aceita‐se entrada manual.

3. **Cadastro de Perfis de Usuário**  
   - Tabela `Intec..tb_PerfilUsuario` lista perfis (ex.: “Coordenador Operacional”, “Supervisor de Roteirização”, “Equipe de Distribuição”, “CRM”).  
   - Relaciona‐se com `Intec..tb_UsuarioPerfil` para determinar permissões de acesso a funcionalidades (inclusão, alteração, cancelamento, consulta).

4. **Cadastro de Motivos Específicos por Tipo**  
   - Em `Intec..tb_CoordenacaoMotivo`, cada registro indica o `tipo_id` e a descrição do motivo (ex.: “Motivo de Segurança”, “Reagendamento Solicitado”).  
   - A aplicação filtra motivos conforme `tipo_id` selecionado.

---

## 7. Segurança, Logs e Auditoria

1. **Controle de Acesso**  
   - Autenticação via domínio corporativo (Active Directory).  
   - Perfis de usuário configurados na aplicação definem rotas/endpoints disponíveis.  
   - Todas as telas de Coordenação exigem login e permissões atribuídas às Filiais/Bases correspondentes.

2. **Log de Auditoria**  
   - Além de `tb_CoordenacaoAcao`, registros de login/logout e tentativas de acesso negado são gravados em `Intec..tb_Auditoria`.  
   - Campos armazenados:  
     - `auditoria_id` (PK)  
     - `usuario_id` (FK)  
     - `acao` (varchar(100))  
     - `data_hora` (datetime)  
     - `ip_origem` (varchar(15))

3. **Criptografia e Proteção de Dados**  
   - Campos sensíveis (como CNPJ, dados de contato) utilizam criptografia simétrica no banco (AES256), conforme política de segurança.  
   - Acesso direto às tabelas via SQL (administradores) deve ter permissão limitada, com logs de consulta em `Intec..tb_LogConsultas`.

---

## 8. Anexos e Recursos Disponíveis

1. **Manual de Coordenação (PDF)**  
   - Consulta rápida de procedimentos operacionais.  
   - Localização:  
     ```
     /?token=__TOKEN_PLACEHOLDER__&download=manual_coordenacao.pdf
     ```

2. **Documentação Completa (DOCX)**  
   - Contém instruções detalhadas, fluxogramas de processo e padrões de nomenclatura.  
   - Localização:  
     ```
     /?token=__TOKEN_PLACEHOLDER__&download=Coordenacao.docx
     ```

3. **Documento de Exibição (PNG)**  
   - Imagens de telas e fluxos de navegação para uso em treinamentos.  
   - Localização:  
     ```
     /?token=__TOKEN_PLACEHOLDER__&download=Documento_Coordenacao.png
     ```

---

## 9. Fluxos de Deploy e Atualizações

1. **Ambientes de Desenvolvimento, Homologação e Produção**  
   - Versão de desenvolvimento publicada em servidor interno `DEV-LuftInforma`.  
   - Após testes funcionais e de regressão, a release é promovida para `HML-LuftInforma`.  
   - Aprovação em homologação aciona deploy automatizado via pipeline (Jenkins/TeamCity) para `PROD-LuftInforma`.

2. **Script de Migração de Banco de Dados**  
   - Alterações de esquema (novas colunas, índices, restrições) seguem padrão de scripts versionados em repositório Git.  
   - Cada deploy refere‐se a um arquivo de migração numerado sequencialmente (`V1.0.1__AddCampoTransitTime.sql`, etc.).  
   - O job de deploy executa esses scripts em sequência, garantindo versão correta do schema.

3. **Validação Pós‐Deploy**  
   - Testes automatizados (unitários e de integração) são executados continuamente.  
   - Um job de smoke test verifica endpoints críticos:  
     - Inclusão de nova coordenação.  
     - Consulta de coordenação existente.  
     - Geração de PDF e envio de e-mail.

---

## 10. Contatos para Suporte Técnico

- **Equipe de Infraestrutura**  
  - E-mail: `infraestrutura@luftlog.com.br`  
  - Responsável por servidores, backups, permissões de rede e manutenção de SMTP.

- **Desenvolvimento LuftInforma**  
  - E-mail: `dev.luftinforma@luftlog.com.br`  
  - Responsável por manutenção de código, correção de bugs, novas funcionalidades.

- **Suporte Operacional (Portal de Transportes)**  
  - E-mail: `suporte.portal@luftlog.com.br`  
  - Contato para dúvidas de uso do sistema, treinamentos e senhas.

- **Equipe de Integração Takeda**  
  - E-mail: `integracao.takeda@luftlog.com.br`  
  - Suporte específico para o processo de coordenação automatizada via arquivos texto.

---

> **Observação Final**  
> Esta documentação foi organizada em duas vertentes: a parte voltada ao usuário, com foco no fluxo operacional e orientações de uso, e a parte técnica, detalhando estruturas de banco, processos automatizados, integrações e governança do sistema. Ambas as seções devem ser consultadas conforme a necessidade — usuário operacional para execução de tarefas diárias e equipe técnica para manutenção, ajustes ou criação de novas funcionalidades.