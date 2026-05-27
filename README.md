# LuftDocs Monorepo

Monorepo para o projeto LuftDocs, consolidando em uma unica raiz:

- `Luft-Docs`: aplicacao web Flask.
- `LuftDocs_API`: API FastAPI usada pelo portal.

## Layout

```text
.
|-- Luft-Docs/
|-- LuftDocs_API/
|-- .githooks/
|-- .github/workflows/
|-- scripts/
|-- CHANGELOG.md
|-- CONTRIBUTING.md
|-- MANIFEST.in
|-- pyproject.toml
|-- requirements.txt
`-- _version.py
```

## Automacoes da raiz

- `ci.yml`: valida Conventional Commits, instala dependencias compartilhadas e verifica sintaxe dos dois apps.
- `release.yml`: a cada merge em `main`, calcula o proximo SemVer, atualiza `_version.py` e `CHANGELOG.md`, publica a release no GitHub e gera a tag automaticamente.
- `deploy.yml`: executa o deploy unificado a partir da release publicada ou via execucao manual, atualizando os dois diretórios e reiniciando os servicos NSSM `LuftDocs` e `LuftDocsAPI`.
- `scripts/release.ps1`: espelha localmente a logica de bump de versao e cria a tag anotada de release.

## Hooks locais

Depois que a raiz estiver versionada como repositorio unico, configure os hooks com:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\install-githooks.ps1
```

## Corte para o repositorio unico

1. Garanta backup ou tag final dos repositorios atuais `Luft-Docs` e `LuftDocs_API`.
2. Antes do primeiro `git add` na raiz, mova ou arquive `Luft-Docs/.git` e `LuftDocs_API/.git`.
3. Crie o novo repositorio Git na raiz atual ou clone o novo remoto diretamente em `C:\Applications\Python\Projetos\LuftDocs`.
4. Adicione o remoto unico do projeto consolidado.
5. Execute `git add .` somente depois de remover os `.git` internos, para evitar gitlinks embutidos.
6. Instale os hooks locais.
7. Ajuste as variaveis do `deploy.yml` se os nomes de servico NSSM ou caminhos do servidor diferirem dos valores padrao.

## Versionamento

- `_version.py` e o `CHANGELOG.md` sao a fonte versionada da release.
- `APP_VERSION` e `API_APP_VERSION` deixaram de ser configuracoes permanentes do `.env`; o runtime agora usa `_version.py`, com overrides locais opcionais via `APP_VERSION_OVERRIDE` e `API_APP_VERSION_OVERRIDE`.

## Observacoes de deploy

- O deploy unificado assume um ambiente virtual compartilhado em `C:\ProjetosPython\LuftDocs\.LUFTDOCS_PACKAGES`.
- O workflow reinicia ambos os servicos no mesmo job; se um deles falhar ao subir, o deploy inteiro falha.
- O runner self-hosted precisa ter `python`, `pip` e `nssm` disponiveis.
