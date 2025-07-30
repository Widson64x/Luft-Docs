# Configuração de EDI: Althaia

Este documento detalha todas as configurações de EDI para o cliente **Althaia**.

---
## Tabela de Configuração de Arquivos

A tabela responde às perguntas: "Mando ou não mando?", "Cliente ou Parceiro?" e "Qual Parceiro?".

| Tipo de EDI | Mando? | Destino | Parceiro / Detalhes |
| :------------- | :----: | :-------: | :----------------------------------- |
| `CONENB` | **Sim** | Parceiro | [[API_ACTIVE]] |
| `OCORRÊNCIAS` | Não | N/A | - |
| `DOCCOB` | Não | N/A | - |
| `PREFDI` | **Sim** | Cliente | Envio direto para o SFTP do cliente |

### Regras de Negócio e Observações
1. A troca do arquivo `CONENB` é feita *exclusivamente* pelo parceiro [[API_ACTIVE]].
2. O arquivo `PREFDI` é gerado e enviado diretamente, sem intermediários.
3. Não há, no momento, processo de `OCORRÊNCIAS` ou `DOCCOB` para este cliente.