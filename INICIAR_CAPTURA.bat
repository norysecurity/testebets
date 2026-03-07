@echo off
echo.
echo  ============================================================
echo   BetAuditor - Capturador mitmproxy para 55QQ
echo  ============================================================
echo.
echo  [1] Iniciando mitmproxy na porta 8080
echo  [2] Chrome sera aberto com proxy configurado
echo  [3] Faca login no 55QQ e jogue normalmente
echo  [4] Tokens serao salvos em logs/
echo.
echo  FECHE ESTA JANELA quando terminar.
echo  ============================================================
echo.

REM Verificar se mitmproxy esta instalado
where mitmdump >nul 2>&1
if errorlevel 1 (
    echo [ERRO] mitmdump nao encontrado.
    echo Rode: pip install mitmproxy
    pause
    exit /b 1
)

REM Abrir Chrome com proxy (usa perfil temporario separado)
echo [*] Abrindo Chrome com proxy 127.0.0.1:8080...
echo [DICA] Se aparecer "Nao Seguro", instale o certificado em http://mitm.it
start "" "chrome.exe" --proxy-server="127.0.0.1:8080" --ignore-certificate-errors --allow-running-insecure-content --user-data-dir="%TEMP%\chrome_proxy_55qq" --new-window "https://55qq2.com/main/inicio"

if errorlevel 1 (
    echo [AVISO] Chrome nao encontrado no PATH, tentando Edge...
    start "" "msedge.exe" --proxy-server="127.0.0.1:8080" --ignore-certificate-errors --allow-running-insecure-content --user-data-dir="%TEMP%\edge_proxy_55qq" "https://55qq2.com/main/inicio"
)

REM Aguardar browser abrir
timeout /t 3 /nobreak >nul

echo [*] Iniciando capturador... (pressione Ctrl+C para parar)
echo.

mitmdump --listen-port 8080 --ssl-insecure --flow-detail 1 --scripts capturador_55qq.py

echo.
echo [OK] Captura encerrada.
echo [OK] Verifique os arquivos em logs\
echo      - tokens_capturados.json
echo      - endpoints_capturados.json
echo      - resumo_final.json
echo.
pause
