@echo off
REM Muda o diretorio para o local do script
cd /d "%~dp0"

REM Ativa o ambiente virtual (garanta que o nome .venv esta correto)
CALL .venv\Scripts\activate

REM Inicia a aplicacao Flask com o Uvicorn
ECHO "Servidor iniciando em http://172.16.200.80:8001"
py run_prod.py

ECHO "Servidor encerrado."
pause