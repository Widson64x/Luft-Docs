# Changelog

Todas as mudancas relevantes deste projeto devem ser registradas aqui.

O formato segue a ideia do Keep a Changelog e o versionamento usa SemVer para as releases automaticas da `main`.

## [Unreleased]

### Pending

- Nenhuma alteracao registrada apos a release mais recente.

## [0.1.0] - 2026-05-27

### Added

- Estrutura inicial do monorepo com `Luft-Docs` e `LuftDocs_API` sob uma unica raiz.
- Hooks versionados em `.githooks`, scripts de validacao e automacoes de CI, release e deploy.
- Template de pull request, arquivo `_version.py` e consolidacao dos metadados de repositorio na raiz.

### Changed

- As configuracoes de ambiente passaram a ser centralizadas em um unico `.env` na raiz.
- `README.md`, `LICENSE`, `.gitignore`, `.gitattributes` e workflows individuais foram removidos dos subprojetos.
