
Componentes notáveis (nomes podem variar conforme branch):
- `Utils/markdown_utils.py`: parser Markdown → HTML com suporte a *wikilinks*.
- `Utils/advanced_filter.py`: filtro de busca com **TF-IDF**.
- `Utils/auth_utils.py`, `Utils/token_utils.py`, `Utils/db_utils.py`: autenticação, tokens e persistência.
- `Routes/*`: **blueprints** que expõem as páginas (home, busca, docs, login, etc.).

---

## Requisitos
- **Python 3.11+**
- Pip / venv
- (Opcional) **SQLite** ou outro banco a gosto (ver `models.py`)
- (Linux, Prod) **gunicorn** e **systemd**
- (Windows, Prod) **pythonw.exe** e **Task Scheduler**

Instale as dependências:

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements.txt
