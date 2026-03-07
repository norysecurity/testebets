@echo off
title IA VIDENTE - HUD EM TEMPO REAL
setlocal

echo ============================================================
echo   IA VIDENTE - Antecipacao de Resultados (v1.0)
echo ============================================================
echo.
echo  [1] Iniciando proxy inteligente na porta 8082...
echo  [2] HUD visual sera injetado nos jogos (Fortune Tiger, Neko, Mines)
echo  [3] O resultado aparecera no topo da tela ANTES do giro parar.
echo.
echo  IMPORTANTE: O certificado mitmproxy deve estar instalado!
echo  (Se nao instalou, acesse http://mitm.it no Chrome do proxy)
echo.
echo  FECHE ESTA JANELA PARA DESATIVAR O VIDENTE.
echo ============================================================
echo.

:: Iniciar o mitmproxy com o script IA_VIDENTE.py
start /b mitmdump -s IA_VIDENTE.py -p 8082 --set block_global=false

:: Abrir o Chrome com proxy configurado e flags de bypass
echo [*] Abrindo Chrome com Vidente Ativado...
start chrome "https://55qq2.com" --proxy-server="127.0.0.1:8082" --ignore-certificate-errors --allow-running-insecure-content --user-data-dir="%temp%\vidente_profile"

pause
