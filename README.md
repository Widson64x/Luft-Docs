# LuftDocs — Plataforma de Documentação Operacional com IA

> **Resumo:** O LuftDocs é um sistema web (Flask) para organizar, versionar e consultar documentação operacional/técnica da empresa. Traz **módulos** com conteúdo funcional e técnico, **busca rápida**, **perfis e permissões**, **histórico de versões** e integrações com **IA (OpenAI, Groq, Gemini)** e **DB vetorial** para perguntas/consultas inteligentes.

---

## ✨ Principais recursos

* **Mapa de conhecimento** por módulos (ex.: *agendamento, coordenação, gestão de risco, LIA*, etc.)
* **Editor de conteúdo** (documento funcional e técnico)
* **Permissões** por perfis/grupos (menu *Gerenciar permissões*)
* **Histórico de versões** com auditoria e backups dos arquivos
* **API REST** (ex.: `/api/modules`) para listagem/paginação/filtragem
* **Busca** e filtros dinâmicos com paginação
* **Integração com IA** (OpenAI, Groq, Gemini) e **DB vetorial** para suporte cognitivo
* **Temas/estilos** com Bootstrap e ícones (Bootstrap Icons)
* **Alertas** (flash messages) com autoclose e botão **X**
* **Transição suave de páginas** e **animação de fundo** personalizável

---

## 🧱 Arquitetura (alto nível)

* **Backend**: Flask + Blueprints

  * `Routes/Core/*`: páginas principais, listagem de módulos, submódulos, index
  * `Routes/Services/*`: download, editor, roteiros, avaliação, etc.
  * `Routes/API/*`: API pública (ex.: `API`, `Permissions`)
  * `LIA_Services/LIA`: camada de IA (modelos + DB vetorial)
* **Frontend**: Jinja2, Bootstrap 5, Bootstrap Icons, CSS/JS estáticos
* **Banco de Dados**: PostgreSQL (recomendado) — também há suporte a MSSQL, se configurado
* **Migrations**: Flask-Migrate (Alembic)
* **Segurança**: CSRF, Rate Limiting (Flask-Limiter), Token de acesso por URL quando necessário

---

## 📁 Estrutura sugerida de pastas (exemplo)

> A distribuição pode variar conforme a sua base. Exemplo de organização:

```
Luft-Docs/
├─ app.py / wsgi.py
├─ Models/
│  ├─ __init__.py
│  ├─ analytics.py
│  ├─ conteudo.py
│  ├─ roteiros.py
│  └─ permissoes.py
├─ LIA_Services/
│  └─ LIA/
├─ Routes/
│  ├─ Core/
│  │  ├─ Main.py (index)
│  │  ├─ Module.py
│  │  └─ SubModule.py
│  ├─ Services/
│  │  ├─ Download.py
│  │  ├─ Editor.py
│  │  ├─ Roteiros.py
│  │  └─ Evaluation.py
│  └─ API/
│     ├─ API.py
│     └─ Permissions.py
├─ static/
│  ├─ CSS/
│  │  └─ Base/Index.css
│  ├─ js/
│  │  └─ alerts.js (opcional)
│  ├─ data/
│  │  └─ icons.json
│  └─ vendor/
│     └─ bootstrap/bootstrap.bundle.min.js
├─ templates/
│  ├─ base.html
│  └─ index.html
├─ migrations/ (Alembic)
├─ requirements.txt
└─ .env
```

---

## ✅ Requisitos

* **Python** 3.10+ (recomendado 3.11)
* **PostgreSQL** 13+ (ou MSSQL, se adaptado)
* **Pip**/venv
* Acesso às **APIs de IA** (opcional): OpenAI, Groq, Gemini

---

## ⚙️ Configuração

Crie um arquivo **`.env`** na raiz. O projeto usa um unico arquivo de ambiente e controla o comportamento por `APP_ENV`, sem ` .env_LOCAL` ou ` .env_PROD`.

Exemplo de variáveis:

```ini
# Aplicacao
APP_ENV=Local
APP_NAME=LuftDocs
APP_VERSION=1.0.0
FLASK_SECRET_KEY=troque-esta-chave
LOG_LEVEL=INFO
BASE_PREFIX=/luft-docs

# Banco principal (PostgreSQL)
PG_USER=seu_usuario
PG_PASS=sua_senha
PG_HOST=localhost
PG_PORT=5432
PG_NAME=luftdocs
PG_DRIVER=postgresql+psycopg
PG_SEARCH_PATH=luftdocst

# Banco de permissoes/diretorio (SQL Server) - opcional
SQL_USER=seu_usuario
SQL_PASS=sua_senha
SQL_HOST=servidor_sql
SQL_PORT=1433
SQL_DB=intec
SQL_DRIVER=mssql+pyodbc
SS_ODBC_DRIVER=ODBC Driver 17 for SQL Server
SQL_DIRECTORY_DB=LuftInforma

# Dados locais/compartilhados
DATA_ROOT=./DATA_LUFTDOCS
DB_PATH=./DATA/luftdocs.db

# API de usuario
USER_API_URL=http://127.0.0.1:9006/luft-api/api

# Integrações de IA (opcionais)
OPENAI_API_KEY=
GROQ_API_KEY=
GEMINI_API_KEY=
OPEN_ROUTER_API_KEY=

# Permissoes e startup
SISTEMA_ID=5
DEBUG_PERMISSIONS=false
CREATE_DATA_DIRS_ON_STARTUP=false
```

> **Dica:** em produção, defina `APP_ENV=Prod`, ajuste `DATA_ROOT` para o compartilhamento correto e use uma `FLASK_SECRET_KEY` forte.

---

## 📦 Instalação

```bash
# 1) Clone
git clone <seu-repo> Luft-Docs
cd Luft-Docs

# 2) Ambiente virtual
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# 3) Dependências
pip install -r requirements.txt

# 4) Banco de dados
flask db upgrade  # aplica migrations (ou crie as tabelas conforme Models)
```

> Se estiver migrando dados/estruturas já existentes, revise permissões do schema e ownership antes dos `ALTER TABLE`.

---

## 🚀 Execução

### Desenvolvimento

```bash
flask run  # padrão: http://127.0.0.1:5000
```

### Produção (Linux) — `gunicorn` + `systemd`

```bash
pip install gunicorn
# app: variável/objeto Flask. Ajuste para "app:app" ou o caminho do factory.
gunicorn -w 4 -b 0.0.0.0:8001 app:app
```

**systemd** (exemplo `/etc/systemd/system/luftdocs.service`):

```ini
[Unit]
Description=LuftDocs (Flask)
After=network.target

[Service]
User=www-data
WorkingDirectory=/opt/Luft-Docs
Environment="PATH=/opt/Luft-Docs/.venv/bin"
EnvironmentFile=/opt/Luft-Docs/.env
ExecStart=/opt/Luft-Docs/.venv/bin/gunicorn -w 4 -b 0.0.0.0:8001 app:app
Restart=always

[Install]
WantedBy=multi-user.target
```

### Produção (Windows) — `waitress` + serviço (NSSM)

```bash
pip install waitress
python -m waitress --listen=0.0.0.0:8001 app:app
```

Use o **NSSM** para transformar em serviço do Windows.

### (Opcional) Nginx como proxy

```nginx
server {
  listen 80;
  server_name docs.suaempresa.com;

  location / {
    proxy_pass http://127.0.0.1:8001;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
  }
}
```

---

## 🔌 API (exemplos)

### `GET /api/modules`

Lista cartões (módulos) com filtro e paginação.

**Parâmetros:**

* `search` *(opcional)* — string para filtrar
* `page` *(opcional)* — número da página (1..N)
* `token` *(opcional)* — token de sessão/acesso quando aplicável

**Exemplo:**

```
GET /api/modules?search=risco&page=2&token=...
```

**Resposta (exemplo):**

```json
{
  "current_page": 2,
  "total_pages": 5,
  "token": "...",
  "cards": [
    { "id": "gestao-de-risco", "nome": "Gestão de Risco", "descricao": "...", "icone": "bi-shield" }
  ]
}
```

> Outros endpoints podem existir (ex.: permissões, editor, export/download). Consulte `Routes/`.

---

## 👤 Perfis & Permissões

* **Menu:** *Gerenciar permissões*
* **Entidades comuns:** Grupos, Usuários, Permissões, Relações (*permissoes\_grupos*, *permissoes\_usuarios*)
* **Regra geral:** ações administrativas (ex.: associar usuário a setor/grupo) exigem papel *Admin*.

---

## 🧠 IA & DB Vetorial

* Suporte a **OpenAI**, **Groq**, **Gemini** (configure chaves no `.env`)
* Carregamento de **DB vetorial** para busca semântica e Q\&A sobre a base documentada
* Pode ser consumido por rotas próprias (ver `LIA_Services/LIA`)

> Mantenha a conformidade com políticas internas para dados sensíveis e logs.

---

## 🎨 UI/UX

* **Bootstrap 5** + **Bootstrap Icons**
* **Alertas (flash)** com `alert-dismissible` e botão **X**
* **Autoclose** de alertas em \~5s (com fallback quando Bootstrap JS não está carregado)
* **Transições de página** para navegação suave
* **Animação de fundo** personalizável via `localStorage`:

  * `ld_bg_quantity` *(padrão: 50)*
  * `ld_bg_speed` *(padrão: 1.0)*
  * `ld_bgAnimation` ∈ {`colisao`, `original`}

---

## 🔧 Troubleshooting

* **Botão X do alerta não fecha**

  * Garanta `class="alert alert-<tipo> alert-dismissible fade show"` no contêiner
  * Carregue `bootstrap.bundle.min.js` **ou** use o fallback de JS (já incluso no template)
* **`Themes.css 404`**

  * Verifique o caminho em `base.html` e se o arquivo existe em `static/CSS/...`
* **Erros de permissão em migrations (`42501`, `must be owner`)**

  * Execute DDL com o **owner** do schema/tabela
  * Evite `session_replication_role` sem permissão de superuser
* **Conexão DB falhando**

  * Confirme variáveis `.env` e alcance de rede
  * Para alta concorrência, considere `NullPool`/pool tuning
* **Rate Limiting (Flask-Limiter) aviso de memória**

  * Configure backend de storage para produção (Redis, etc.)

---

## 🗺️ Roadmap (sugestão)

* Painel de métricas (uso, módulos mais acessados, erros)
* Workflow de aprovação com múltiplas etapas
* Export/Import de módulos (JSON/YAML)
* Auditoria avançada (diff de versões)
* i18n (multi-idioma)

---

## 🤝 Contribuição

1. Crie um branch a partir de `main`
2. Faça commits atômicos e mensagens claras
3. Abra um PR descrevendo **o problema** e **a solução**

---

## 🔒 Licença

Defina a licença conforme a política da empresa (ex.: **Proprietária/Interna**). Caso público, sugere-se **MIT** ou similar.

---

## 📸 Créditos & Agradecimentos

* Equipe de Sistemas/Engenharia LUFT
* Usuários que contribuíram com módulos e revisões

> Dúvidas? Abra uma issue interna ou fale com o time responsável pelo LuftDocs.
