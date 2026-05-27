# Plano de Migracao de Nomenclatura do Banco

## Objetivo

Renomear tabelas e colunas do PostgreSQL para o padrao `Tb_Docs_...`, com nomes em pt-BR, sem perda de dados.

Schema alvo atual: `luftdocst`.

## Estrategia adotada

1. Fase 1: renomeacao fisica no PostgreSQL com `ALTER TABLE ... RENAME` e `ALTER TABLE ... RENAME COLUMN`.
2. Fase 2: ajuste do runtime Python/SQLAlchemy para apontar para os nomes novos.
3. Rollback: executar o mesmo script com `--reverter`.

## O que este pacote entrega

- `mapa_renomeacao_docs.py`: manifesto oficial de tabelas e colunas.
- `renomear_nomenclatura_postgres.py`: executor transacional com `dry-run` e rollback.

## Ordem segura de execucao

1. Validar o manifesto em `Scripts/Banco/mapa_renomeacao_docs.py`.
1. Fazer backup do schema `luftdocst` no PostgreSQL.
1. Rodar dry-run:

```powershell
python .\Scripts\Banco\renomear_nomenclatura_postgres.py
```

1. Validar se o SQL gerado bate com a expectativa.
1. Executar em janela controlada:

```powershell
python .\Scripts\Banco\renomear_nomenclatura_postgres.py --aplicar
```

1. Depois da renomeacao fisica, atualizar os models e os pontos do codigo que ainda usam nomes antigos.

## Observacoes importantes

- O script atual trata apenas PostgreSQL principal.
- O schema padrao do executor e `luftdocst`.
- O script nao renomeia sequences, indexes ou constraints nominais. Isso nao causa perda de dados nem quebra funcional imediata, mas pode ser feito numa etapa posterior para limpeza completa de naming.
- Existem bancos SQLite auxiliares no projeto, mas eles estao fora do escopo desta fase.
- Qualquer SQL bruto fora do ORM deve ser revisado antes do cutover final.

## Rollback

```powershell
python .\Scripts\Banco\renomear_nomenclatura_postgres.py --aplicar --reverter
```

## Proximo passo esperado

Depois de homologar o rename fisico, a proxima tarefa e atualizar `Models.py` e os usos de atributos para refletir os nomes novos de tabelas e colunas.
