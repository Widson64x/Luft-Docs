# 🗂️ Luft-Docs — Wiki & Documentação Interna
> Plataforma leve para **organização de conhecimento**, busca e publicação de **documentos em Markdown/HTML** dentro da rede LUFT. Feito em **Python + Flask** com templates **Jinja**, servindo páginas estáticas e dinâmicas, além de utilitários para autenticação, histórico de buscas e filtros avançados.

<p align="center">
  <a href="https://www.python.org/"> <img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white"> </a>
  <a href="https://flask.palletsprojects.com/"> <img alt="Flask" src="https://img.shields.io/badge/Flask-2.x-000?logo=flask&logoColor=white"> </a>
  <a href="#licença"> <img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue"> </a>
</p>

---

## Visão Geral
**Luft-Docs** centraliza páginas, manuais e playbooks da operação. Você pode escrever em **Markdown** (com suporte a *wikilinks*) ou HTML, organizar por módulos e disponibilizar uma **busca** que prioriza relevância (TF-IDF). O projeto expõe rotas Flask simples, com separação por camadas (**Routes**, **Templates**, **Utils**, **DATA**) e executáveis para ambientes Windows e Linux.

### Principais recursos
- ✍️ **Markdown/HTML** com conversão para HTML e suporte a *wikilinks* (ex.: `[[Página/Alvo]]`).
- 🔎 **Busca inteligente** com filtro avançado (TF-IDF) e histórico por usuário.
- 👤 **Autenticação** básica e **controle de acesso por módulo**.
- 🧩 Estrutura modular (rotas, serviços/utilitários, templates, estáticos).
- 🖼️ **Templates** Jinja prontos para UI dark/light, com assets em `Static/`.
- 🗄️ **Armazenamento de conteúdo** em `DATA/` (arquivos Markdown/HTML/JSON).
- 🚀 **Execução simples** (Windows via `start_app.bat`/`pythonw.exe` e Linux via `gunicorn + systemd`).

> **Obs.** Os nomes de diretórios/arquivos aqui refletem a árvore atual do repositório. Ajuste conforme sua instalação.

---

## Arquitetura & Pastas
A estrutura do projeto é enxuta e previsível:

