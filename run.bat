@echo off
REM Script para executar a aplicacao SEF
REM Uso: Duplo clique neste arquivo ou execute "run.bat" no terminal

cd /d "%~dp0"
python src\main.py
pause
