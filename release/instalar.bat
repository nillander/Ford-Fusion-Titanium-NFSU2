@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

set "CANDIDATOS=%TEMP%\fusion-nfsu2-pastas.txt"
set "PERGUNTADAS=%TEMP%\fusion-nfsu2-perguntadas.txt"
if exist "%CANDIDATOS%" del /f /q "%CANDIDATOS%"
if exist "%PERGUNTADAS%" del /f /q "%PERGUNTADAS%"

set "SLOT=MUSTANGGT"
if /i "%~1"=="2012" set "SLOT=FOCUS"
if not exist "%~dp0CARS\MUSTANGGT\GEOMETRY.BIN" if exist "%~dp0CARS\FOCUS\GEOMETRY.BIN" set "SLOT=FOCUS"
set "RAIZ=%~dp0"
if exist "%~dp0CARS\!SLOT!\GEOMETRY.BIN" goto TemCarro
if exist "%~dp0..\CARS\!SLOT!\GEOMETRY.BIN" (
    set "RAIZ=%~dp0..\"
    goto TemCarro
)
echo Nao encontrei CARS\!SLOT!\GEOMETRY.BIN ao lado deste script:
echo %~dp0
pause
exit /b 1

:TemCarro
if not exist "!RAIZ!CARS\!SLOT!\TEXTURES.BIN" (
    echo Nao encontrei CARS\!SLOT!\TEXTURES.BIN
    pause
    exit /b 1
)
set "MENSAGEM=O Fusion 2018 AWD substitui o Ford Mustang GT."
if /i "!SLOT!"=="FOCUS" set "MENSAGEM=O Fusion 2012 FWD substitui o Ford Focus."

echo Procurando Need for Speed: Underground 2...
echo.

call :DoRegistro "HKLM\SOFTWARE\WOW6432Node\EA GAMES\Need for Speed Underground 2"
call :DoRegistro "HKLM\SOFTWARE\EA GAMES\Need for Speed Underground 2"
call :DoRegistro "HKLM\SOFTWARE\WOW6432Node\Electronic Arts\Need for Speed Underground 2"
call :DoRegistro "HKLM\SOFTWARE\Electronic Arts\Need for Speed Underground 2"

call :Testar "C:\Program Files (x86)\EA GAMES\Need for Speed Underground 2"
call :Testar "C:\Program Files\EA GAMES\Need for Speed Underground 2"
call :Testar "C:\Program Files (x86)\Electronic Arts\Need for Speed Underground 2"
call :Testar "C:\Program Files\Electronic Arts\Need for Speed Underground 2"
call :Testar "D:\Program Files (x86)\EA GAMES\Need for Speed Underground 2"
call :Testar "D:\Program Files (x86)\Electronic Arts\Need for Speed Underground 2"
call :Testar "C:\Jogos\Need for Speed Underground 2"
call :Testar "D:\Jogos\Need for Speed Underground 2"
call :Testar "D:\Games\Need for Speed Underground 2"

call :Steam

if exist "%CANDIDATOS%" call :PerguntarLista
if not errorlevel 1 exit /b 0

echo Procurando SPEED2.EXE nos discos fixos. Isso pode demorar.
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$seen = @{}; Get-Content -LiteralPath $env:TEMP'\fusion-nfsu2-pastas.txt' -ErrorAction SilentlyContinue | ForEach-Object { $seen[$_.TrimEnd('\').ToLower()] = $true }; Get-CimInstance Win32_LogicalDisk -Filter \"DriveType=3\" | ForEach-Object { Get-ChildItem -LiteralPath ($_.DeviceID + '\') -Filter SPEED2.EXE -Recurse -File -ErrorAction SilentlyContinue | ForEach-Object { $dir = $_.DirectoryName; $key = $dir.TrimEnd('\').ToLower(); if (-not $seen.ContainsKey($key) -and (Test-Path -LiteralPath (Join-Path $dir 'CARS')) -and (Test-Path -LiteralPath (Join-Path $dir 'GLOBAL\GlobalB.lzc'))) { $seen[$key] = $true; Add-Content -LiteralPath $env:TEMP'\fusion-nfsu2-pastas.txt' -Value $dir -Encoding ascii } } }"

if not exist "%CANDIDATOS%" goto Manual
call :PerguntarLista
if not errorlevel 1 exit /b 0

:Manual
echo.
set "DIGITADA="
set /p DIGITADA=Digite a pasta do jogo, ou Enter para cancelar: 
if not defined DIGITADA exit /b 1
call :Confirmar "%DIGITADA%"
if errorlevel 1 (
    echo Instalacao cancelada.
    pause
    exit /b 1
)
exit /b 0

:DoRegistro
set "CHAVE=%~1"
for /f "tokens=3,*" %%A in ('reg query "%CHAVE%" /v "Install Dir" 2^>nul') do (
    if /i "%%A"=="REG_SZ" call :Testar "%%B"
)
exit /b 0

:Steam
set "STEAM="
for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v SteamPath 2^>nul') do (
    if /i "%%A"=="REG_SZ" set "STEAM=%%B"
)
if not defined STEAM exit /b 0
set "STEAM=!STEAM:/=\!"
call :Testar "!STEAM!\steamapps\common\Need for Speed Underground 2"
if not exist "!STEAM!\steamapps\libraryfolders.vdf" exit /b 0
for /f "usebackq delims=" %%P in (`powershell -NoProfile -Command "$p='%STEAM%\steamapps\libraryfolders.vdf'; if (Test-Path -LiteralPath $p) { Select-String -LiteralPath $p -Pattern '\"path\"\s+\"([^\"]+)\"' -AllMatches | ForEach-Object { $_.Matches } | ForEach-Object { $_.Groups[1].Value.Replace('\\\\','\') } }"`) do (
    call :Testar "%%P\steamapps\common\Need for Speed Underground 2"
)
exit /b 0

:Testar
set "PASTA=%~1"
if not defined PASTA exit /b 0
if "!PASTA:~-1!"=="\" set "PASTA=!PASTA:~0,-1!"
if not exist "!PASTA!\SPEED2.EXE" exit /b 0
if not exist "!PASTA!\CARS" exit /b 0
if not exist "!PASTA!\GLOBAL\GlobalB.lzc" exit /b 0
if not exist "%CANDIDATOS%" (
    >>"%CANDIDATOS%" echo !PASTA!
    exit /b 0
)
findstr /L /I /X /C:"!PASTA!" "%CANDIDATOS%" >nul
if errorlevel 1 >>"%CANDIDATOS%" echo !PASTA!
exit /b 0

:PerguntarLista
for /f "usebackq delims=" %%G in ("%CANDIDATOS%") do (
    findstr /L /I /X /C:"%%G" "%PERGUNTADAS%" >nul 2>&1
    if errorlevel 1 (
        call :Confirmar "%%G"
        if not errorlevel 1 exit /b 0
    )
)
exit /b 1

:Confirmar
set "JOGO=%~1"
if not exist "!JOGO!\SPEED2.EXE" (
    echo.
    echo Essa pasta nao tem SPEED2.EXE:
    echo !JOGO!
    exit /b 1
)
>>"%PERGUNTADAS%" echo !JOGO!
echo.
echo Pasta encontrada:
echo !JOGO!
set "RESP="
set /p RESP=Esta pasta esta correta? (S/N) 
if /i "!RESP!"=="S" goto Instalar
if /i "!RESP!"=="SIM" goto Instalar
exit /b 1

:Instalar
echo.
echo Feche o jogo se ele estiver aberto.
echo Copiando CARS\!SLOT! para:
echo !JOGO!
if not exist "!JOGO!\CARS\!SLOT!" mkdir "!JOGO!\CARS\!SLOT!"
for %%F in (GEOMETRY.BIN TEXTURES.BIN) do (
    if exist "!JOGO!\CARS\!SLOT!\%%F" if not exist "!JOGO!\CARS\!SLOT!\%%F.antes-fusion" copy /y "!JOGO!\CARS\!SLOT!\%%F" "!JOGO!\CARS\!SLOT!\%%F.antes-fusion" >nul
)
robocopy "!RAIZ!CARS\!SLOT!" "!JOGO!\CARS\!SLOT!" GEOMETRY.BIN TEXTURES.BIN /R:1 /W:1
if errorlevel 8 goto Falhou
call :AplicarGlobalB
if errorlevel 1 goto FalhouGlobalB
echo.
echo Instalacao concluida.
echo !MENSAGEM!
pause
exit /b 0

:AplicarGlobalB
set "FUSION_SLOT=!SLOT!"
set "FUSION_IN=!JOGO!\GLOBAL\GlobalB.lzc"
set "FUSION_OUT=!JOGO!\GLOBAL\GlobalB.lzc.fusion-novo"
if not exist "!FUSION_IN!" (
    echo Nao encontrei GLOBAL\GlobalB.lzc
    exit /b 1
)
if not exist "!JOGO!\GLOBAL\GlobalB.lzc.antes-fusion" (
    copy /y "!FUSION_IN!" "!JOGO!\GLOBAL\GlobalB.lzc.antes-fusion" >nul
    if errorlevel 1 exit /b 1
    set "FEZBACKUP=1"
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0globalb_patch.ps1"
if errorlevel 1 (
    echo.
    echo Nao foi possivel ajustar o GlobalB. Os arquivos do carro ja foram copiados.
    if exist "!FUSION_OUT!" del /f /q "!FUSION_OUT!"
    exit /b 1
)
move /y "!FUSION_OUT!" "!FUSION_IN!" >nul
if errorlevel 1 exit /b 1
if defined FEZBACKUP echo O GlobalB anterior foi salvo como GLOBAL\GlobalB.lzc.antes-fusion
exit /b 0

:FalhouGlobalB
echo.
pause
exit /b 1

:Falhou
echo.
echo A copia falhou. Feche o jogo e execute o script de novo.
pause
exit /b 1

exit /b 0
