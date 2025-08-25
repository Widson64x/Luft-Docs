# 🗂️ Luft‑Docs — Wiki & Documentação Interna

> Plataforma leve para **organização de conhecimento**, com busca e publicação de **documentos Markdown/HTML** dentro da rede LUFT.

<p align="center">
  <a href="https://www.python.org/"><img alt="Python" src="https://img.shields.io/badge/Python-3.11+-3776AB?logo=python&logoColor=white"></a>
  <a href="https://flask.palletsprojects.com/"><img alt="Flask" src="https://img.shields.io/badge/Flask-2.x-000?logo=flask&logoColor=white"></a>
  <img alt="OS" src="https://img.shields.io/badge/OS-Windows%20%7C%20Linux-informational">
  <a href="#licenca"><img alt="License" src="https://img.shields.io/badge/License-Apache%202.0-blue"></a>
</p>

---

## Sumário

* [Visão Geral](#visão-geral)
* [Recursos](#recursos)
* [Arquitetura & Estrutura de Pastas](#arquitetura--estrutura-de-pastas)
* [Stack](#stack)
* [Pré‑requisitos](#pré-requisitos)
* [Instalação](#instalação)
* [Configuração (.env)](#configuração-env)
* [Execução em Desenvolvimento](#execução-em-desenvolvimento)
* [Produção em Linux (gunicorn + systemd)](#produção-em-linux-gunicorn--systemd)
* [Reverse Proxy (opcional, Nginx)](#reverse-proxy-opcional-nginx)
* [Produção em Windows (pythonw.exe + Task Scheduler)](#produção-em-windows-pythonwexe--task-scheduler)
* [Conteúdo & Dados (`DATA/`)](#conteúdo--dados-data)
* [Logs & Observabilidade](#logs--observabilidade)
* [Backup & Restore](#backup--restore)
* [Testes](#testes)
* [Roadmap](#roadmap)
* [Contribuição](#contribuição)
* [Licença](#licença)
* [Créditos](#créditos)

---

## Visão Geral

**Luft‑Docs** centraliza páginas, manuais, procedimentos e playbooks da operação. Os conteúdos são escritos em **Markdown** (com *wikilinks* `[[Pagina/Alvo]]`) ou HTML e organizados em módulos. A aplicação expõe rotas Flask simples e separação por camadas (**Routes**, **Templates**, **Utils**, **DATA**), permitindo execução em Windows ou Linux.

### Caso de uso

* Documentação interna por áreas (Operação, TI, Comercial).
* Publicação rápida de manuais e POPs.
* Busca textual com priorização por relevância.

---

## Recursos

* ✍️ **Markdown/HTML** → renderização para HTML; suporte a *wikilinks* (`[[...]]`).
* 🔎 **Busca**: filtro por termo com priorização (TF‑IDF leve) e histórico por usuário.
* 👤 **Autenticação** básica e **controle de acesso por módulo**.
* 🧩 **Arquitetura modular**: rotas, utilitários, templates, estáticos.
* 🗄️ **DATA/**: pasta única para conteúdo, anexos e banco SQLite.
* 🚀 **Deploy simples**: `gunicorn + systemd` (Linux) ou `pythonw.exe + Task Scheduler` (Windows) **sem console**.

> Observação: adapte o README aos nomes de arquivos/dirs que estiverem no seu branch.

---

## Arquitetura & Estrutura de Pastas

```
Luft-Docs/
├─ App.py                 # Entrypoint Flask (dev)
├─ run_prod.py            # Entrypoint para produção (opcional)
├─ Config.py              # Configurações centrais (paths, flags)
├─ models.py              # Modelos (ex.: usuários, histórico)
├─ Routes/                # Blueprints e rotas (home, busca, docs, auth)
├─ Templates/             # Jinja templates (views)
├─ Static/                # CSS, JS, imagens
├─ Utils/                 # Markdown, busca, auth, helpers
├─ DATA/                  # Conteúdo (docs, anexos), logs e banco
├─ requirements.txt       # Dependências
└─ start_app.bat          # Inicialização no Windows
```

Componentes úteis (nomes podem variar):

* `Utils/markdown_utils.py`: Markdown → HTML com *wikilinks*.
* `Utils/advanced_filter.py`: busca com TF‑IDF básico.
* `Utils/auth_utils.py` e `Utils/db_utils.py`: autenticação e persistência.

---

## Stack

* **Linguagem**: Python 3.11+
* **Web**: Flask 2.x + Jinja2
* **Banco**: SQLite (padrão) — pode trocar por outro via `DATABASE_URL`
* **Servidor (prod)**: gunicorn (Linux) ou pythonw\.exe + Task Scheduler (Windows)

---

## Pré‑requisitos

* Python **3.11+**
* Pip / venv
* (Linux) `systemd` e, opcional, **Nginx** para TLS/reverse proxy
* (Windows) **Task Scheduler**

---

## Instalação

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
```

---

## Configuração (.env)

Crie um arquivo `.env` na raiz (ou ajuste diretamente `Config.py`):

```ini
# Segurança
SECRET_KEY=troque-esta-chave

# Aplicação
FLASK_ENV=production
APP_HOST=0.0.0.0
APP_PORT=8001

# Caminhos
BASE_DATA_DIR=./DATA
BASE_STATIC_DIR=./Static
BASE_TEMPLATES_DIR=./Templates
LOG_DIR=./DATA/logs

# Banco (ajuste conforme seu models/ORM)
DATABASE_URL=sqlite:///./DATA/luftdocs.db
```

> Se não usar `.env`, defina as variáveis no SO ou em `Config.py`.

---

## Execução em Desenvolvimento

```bash
# venv ativo
python App.py
# ou, se houver factory
# flask --app App:app run --host=0.0.0.0 --port=8001
```

Acesse: `http://127.0.0.1:8001/`.

---

## Produção em Linux (gunicorn + systemd)

### Gunicorn local (teste)

```bash
pip install gunicorn
gunicorn "App:app" -w 2 -b 0.0.0.0:8001 --timeout 120
```

### Service systemd (`/etc/systemd/system/luftdocs.service`)

```ini
[Unit]
Description=Luft-Docs (Flask + Gunicorn)
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/opt/Luft-Docs
Environment="PYTHONUNBUFFERED=1"
Environment="FLASK_ENV=production"
Environment="APP_PORT=8001"
ExecStart=/opt/Luft-Docs/.venv/bin/gunicorn "App:app" -w 2 -b 0.0.0.0:8001 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable luftdocs
sudo systemctl start luftdocs
sudo systemctl status luftdocs
```

> Dica: crie usuário dedicado, permissões mínimas e use um reverse proxy para TLS.

---

## Reverse Proxy (opcional, Nginx)

`/etc/nginx/sites-available/luftdocs.conf`:

```nginx
server {
    listen 80;
    server_name _;

    location /healthz { return 200 'ok'; add_header Content-Type text/plain; }

    location / {
        proxy_pass http://127.0.0.1:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/luftdocs.conf /etc/nginx/sites-enabled/luftdocs.conf
sudo nginx -t && sudo systemctl reload nginx
```

---

## Produção em Windows (pythonw\.exe + Task Scheduler)

### Script silencioso (`run_silent.cmd`)

```bat
@echo off
SET BASE=C:\Projetos\Luft-Docs
CALL %BASE%\.venv\Scripts\activate.bat
pythonw.exe %BASE%\App.py
```

### Agendador (Windows em inglês)

1. **Task Scheduler** → *Create Task…*
2. **General**: marque “Run whether user is logged on or not” e “Run with highest privileges”.
3. **Triggers**: *At startup*.
4. **Actions**: *Start a program* → `cmd.exe /C "C:\Projetos\Luft-Docs\run_silent.cmd"`.
5. **Conditions**: desmarque “Start the task only if the computer is on AC power” (se servidor).
6. **Settings**: habilite “If the task fails, restart every 1 minute” (3 tentativas).

> Alternativamente, use `start_app.bat` já incluso e ajuste caminhos.

---

## Conteúdo & Dados (`DATA/`)

```
DATA/
├─ docs/        # páginas .md/.html
├─ media/       # imagens, PDFs, anexos
├─ indices/     # artefatos de busca (tf-idf, dicionários)
├─ logs/        # arquivos de log da aplicação
└─ users/       # dados auxiliares (histórico, preferências)
```

Boas práticas:

* Versione **apenas** modelos/estruturas, não suba dados sensíveis.
* Configure backup periódico (ver seção abaixo).

---

## Logs & Observabilidade

* Logs em `DATA/logs/` (ou `LOG_DIR`).
* Integração fácil com **Grafana Loki**/ELK via filebeat.
* **Healthcheck** simples (exemplo de rota):

  ```python
  @app.get("/healthz")
  def healthz():
      return {"status": "ok"}, 200
  ```

---

## Backup & Restore

### Backup

```bash
# Parar serviço (Linux)
sudo systemctl stop luftdocs

# Compactar DATA e dependências do app
cd /opt
sudo tar -czf luftdocs-backup_$(date +%F).tar.gz Luft-Docs/DATA Luft-Docs/requirements.txt Luft-Docs/Config.py

# Iniciar novamente
sudo systemctl start luftdocs
```

### Restore

```bash
sudo systemctl stop luftdocs
sudo tar -xzf luftdocs-backup_YYYY-MM-DD.tar.gz -C /opt/
sudo systemctl start luftdocs
```

> Para **SQLite**, o arquivo do banco fica dentro de `DATA/` (ex.: `luftdocs.db`).

---

## Testes

Estrutura sugerida com **pytest**:

```
tests/
├─ test_auth.py
├─ test_docs.py
├─ test_search.py
└─ conftest.py
```

```bash
pip install pytest
pytest -q
```

---

## Roadmap

* [ ] Indexador incremental de conteúdo (watchdog).
* [ ] Upload/edição de páginas via UI com histórico de versões.
* [ ] Busca com operadores (AND/OR/NOT), *highlight* e *snippets*.
* [ ] SSO corporativo (AD/LDAP/OIDC).
* [ ] Exportação de páginas para PDF.
* [ ] Temas light/dark com *switcher*.

---

## Contribuição

1. Crie uma *branch* por feature/bugfix.
2. Siga **PEP 8** e *type hints* quando fizer sentido.
3. Adicione testes ao alterar regras de negócio.
4. Abra PR com contexto, escopo e screenshots.

---

## Licença

<a id="licenca"></a>
Licenciado sob **Apache 2.0**. Consulte `LICENSE` para detalhes.

---

## Créditos

Desenvolvido por **Widson Rodrigues — LUFT**. 🙌
