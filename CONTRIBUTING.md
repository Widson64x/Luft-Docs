# Contribuindo com o LuftDocs Monorepo

## Objetivo

Este documento define o minimo operacional para contribuir com seguranca e previsibilidade no monorepo do LuftDocs.

## Ambiente local

1. Crie a virtualenv e ative o ambiente compartilhado do projeto.
1. Ajuste o arquivo `.env` da raiz com os valores locais ou de homologacao.
1. Garanta acesso autenticado ao repositorio privado `Widson64x/LuftCore`.
1. Instale as dependencias com `python -m pip install -r requirements.txt` e `python -m pip install -r LuftDocs_API/requirements.txt`.
1. Execute `powershell -ExecutionPolicy Bypass -File .\scripts\install-githooks.ps1` uma vez por clone.

## Regras de contribuicao

1. Nao committe `.env`, tokens, segredos de Vault ou credenciais embedadas em URLs.
1. Prefira alteracoes pequenas, reversiveis e validadas localmente antes de abrir PR.
1. Preserve o desenho do monorepo: a raiz concentra automacao, `Luft-Docs` contem a aplicacao Flask e `LuftDocs_API` contem a API FastAPI.
1. Quando alterar comportamento de banco, autenticacao, runner ou deploy, atualize a documentacao correspondente.
1. Se precisar de dados sensiveis para reproduzir um cenario, use valores ficticios ou placeholders.

## Branches e commits

1. Use nomes de branch objetivos, por exemplo: `feature/...`, `fix/...`, `build/...` ou `hotfix/...`.
1. Escreva commits no padrao Conventional Commits.
1. Evite misturar refactor, ajuste funcional e infraestrutura no mesmo commit quando isso prejudicar a revisao.

## Validacao minima

Antes de abrir PR ou enviar para homologacao:

1. Execute o fluxo principal impactado pela alteracao.
1. Rode ao menos uma validacao automatizada local, como `python -m compileall _version.py scripts Luft-Docs LuftDocs_API`.
1. Se alterou bootstrap, configuracao ou entry points, rode tambem `python -m py_compile Luft-Docs/App.py Luft-Docs/Wsgi.py LuftDocs_API/Wsgi.py LuftDocs_API/App/Main.py`.
1. Revise se os hooks `commit-msg` e `pre-push` estao ativos e se nao ha arquivos sensiveis staged.

## Releases e deploy

1. Toda nova merge em `main` gera uma release automatica com bump semantico de versao.
1. O bump segue Conventional Commits: `feat` sobe `minor`, `fix` sobe `patch` e `!` ou `BREAKING CHANGE` sobe `major`.
1. O deploy produtivo parte da release publicada no GitHub, nao de uma tag criada manualmente dentro dos subprojetos.

## Pull requests

1. Descreva o problema resolvido e o risco residual.
1. Liste como a alteracao foi validada.
1. Se houver impacto operacional, mencione ajustes necessarios em `.env`, Vault, runner, NSSM ou permissao de acesso.
