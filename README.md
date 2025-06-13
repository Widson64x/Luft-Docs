# WIKIDOCS



├── config.py
│
├── data/
│   ├── modules/
│   └── global/
│
└── utils/
    ├── auth/
    │   ├── __init__.py
    │   ├── db_utils.py        # conexão e verificação de usuários
    │   ├── token_utils.py     # geração e validação de tokens
    │   └── auth_utils.py      # decorators e fluxo de login/logout
    │
    ├── data/
    │   ├── __init__.py
    │   ├── search_history.py  # histórico de buscas
    │   ├── module_access.py   # controle de acessos
    │   └── modulo_utils.py    # carregamento de módulos e markdown
    │
    └── text/
        ├── __init__.py
        ├── markdown_utils.py  # parser de wikilinks e conversão Markdown→HTML
        └── advanced_filter.py  # classe de filtro avançado (TF-IDF)