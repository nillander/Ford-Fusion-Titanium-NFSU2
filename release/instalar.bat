@echo off
setlocal EnableExtensions EnableDelayedExpansion
chcp 65001 >nul
cd /d "%~dp0"

set "CANDIDATOS=%TEMP%\fusion-nfsu2-pastas.txt"
set "PERGUNTADAS=%TEMP%\fusion-nfsu2-perguntadas.txt"
if exist "%CANDIDATOS%" del /f /q "%CANDIDATOS%"
if exist "%PERGUNTADAS%" del /f /q "%PERGUNTADAS%"

set "RAIZ=%~dp0"
if exist "%~dp0CARS\MUSTANGGT\GEOMETRY.BIN" goto TemCarro
if exist "%~dp0..\CARS\MUSTANGGT\GEOMETRY.BIN" (
    set "RAIZ=%~dp0..\"
    goto TemCarro
)
echo Nao encontrei CARS\MUSTANGGT\GEOMETRY.BIN ao lado deste script:
echo %~dp0
pause
exit /b 1

:TemCarro
if not exist "!RAIZ!CARS\MUSTANGGT\TEXTURES.BIN" (
    echo Nao encontrei CARS\MUSTANGGT\TEXTURES.BIN
    pause
    exit /b 1
)
set "MENSAGEM=O Fusion 2018 substitui o Ford Mustang."

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
echo Copiando CARS\MUSTANGGT para:
echo !JOGO!
if not exist "!JOGO!\CARS\MUSTANGGT" mkdir "!JOGO!\CARS\MUSTANGGT"
robocopy "!RAIZ!CARS\MUSTANGGT" "!JOGO!\CARS\MUSTANGGT" GEOMETRY.BIN TEXTURES.BIN /R:1 /W:1
if errorlevel 8 goto Falhou
call :AplicarGlobalB
if errorlevel 1 goto FalhouGlobalB
echo.
echo Instalacao concluida.
echo !MENSAGEM!
pause
exit /b 0

:AplicarGlobalB
set "FUSION_BAT=%~f0"
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
powershell -NoProfile -ExecutionPolicy Bypass -Command "$raw = [IO.File]::ReadAllText($env:FUSION_BAT); $i = $raw.LastIndexOf('# BEGIN-FUSION-PATCH'); if ($i -lt 0) { exit 2 }; Invoke-Expression $raw.Substring($i)"
if errorlevel 3 (
    echo.
    echo O GlobalB.lzc esta compactado. Salve-o descompactado no Nikki e execute de novo.
    echo Os arquivos do carro ja foram copiados.
    exit /b 1
)
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

# BEGIN-FUSION-PATCH
$ErrorActionPreference = 'Stop'
try {
  $Src = $env:FUSION_IN
  $Dst = $env:FUSION_OUT
  $REC = 2192
  $D = [System.IO.File]::ReadAllBytes($Src)
  if ($D.Length -ge 4 -and $D[0] -eq 0x4A -and $D[1] -eq 0x44 -and $D[2] -eq 0x4C -and $D[3] -eq 0x5A) {
    [Console]::Error.WriteLine('GlobalB esta compactado (JDLZ).')
    [Environment]::Exit(3)
  }
  $found = New-Object System.Collections.Generic.List[object]
  function Walk([int]$start, [int]$end) {
    $p = $start
    while (($p + 8) -le $end) {
      $cid = [BitConverter]::ToUInt32($D, $p)
      $sz = [BitConverter]::ToInt32($D, $p + 4)
      if ($cid -eq 0x34600) { $script:found.Add(@($p, $sz)) | Out-Null }
      if (($cid -band 0x80000000) -ne 0) { Walk ($p + 8) ($p + 8 + $sz) }
      $p += 8 + $sz
    }
  }
  Walk 0 $D.Length
  if ($found.Count -eq 0) { throw 'Chunk 0x34600 nao encontrado.' }
  $last = $found[$found.Count - 1]
  $base = $last[0] + 8
  $size = $last[1]
  $recs = @{}
  for ($off = $base + 8; $off + $REC -le $base + $size; $off += $REC) {
    $name = [System.Text.Encoding]::ASCII.GetString($D, $off, 32).Split([char]0)[0]
    $recs[$name] = $off
  }
  foreach ($need in @('MUSTANGGT','COROLLA','LANCEREVO8')) {
    if (-not $recs.ContainsKey($need)) { throw "Registro $need ausente no GlobalB." }
  }
  $F = $recs['MUSTANGGT']; $C = $recs['COROLLA']; $L = $recs['LANCEREVO8']
  function Copy-Range([int]$srcOff, [int]$a, [int]$b) {
    [Buffer]::BlockCopy($D, $srcOff + $a, $D, $F + $a, $b - $a)
  }
  Copy-Range $L 272 288
  for ($w = 0; $w -lt 4; $w++) { Copy-Range $L (288 + 48 * $w + 28) (288 + 48 * $w + 36) }
  Copy-Range $L 480 704
  Copy-Range $L 880 992
  Copy-Range $L 1616 2032
  Copy-Range $C 704 880
  Copy-Range $C 992 1616
  function Get-PeakKw([int]$rec) {
    $maxRpm = [double][BitConverter]::ToSingle($D, $rec + 776)
    $best = [double]::NegativeInfinity
    for ($k = 0; $k -lt 9; $k++) {
      $t = [double][BitConverter]::ToSingle($D, $rec + 784 + 4 * $k)
      $p = $t * $maxRpm * $k / 8 * 2 * [Math]::PI / 60
      if ($p -gt $best) { $best = $p }
    }
    return $best
  }
  $power = (248 * 0.73549875) / (Get-PeakKw $C)
  $arrays = @(
    @(784,820), @(820,856), @(992,1100),
    @(1328,1376), @(1392,1440), @(1456,1504), @(1520,1568), @(1572,1604)
  )
  foreach ($pair in $arrays) {
    for ($o = $pair[0]; $o -lt $pair[1]; $o += 4) {
      $scaled = [single]([double][BitConverter]::ToSingle($D, $C + $o) * $power)
      [Buffer]::BlockCopy([BitConverter]::GetBytes($scaled), 0, $D, $F + $o, 4)
    }
  }
  foreach ($o in @(720,1136,1200,1264)) { Copy-Range $L $o ($o + 4) }
  $wheels = @(@(1.431,0.78), @(1.431,-0.78), @(-1.311,-0.78), @(-1.311,0.78))
  for ($i = 0; $i -lt 4; $i++) {
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]$wheels[$i][0]), 0, $D, $F + 288 + 48 * $i, 4)
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]$wheels[$i][1]), 0, $D, $F + 288 + 48 * $i + 4, 4)
  }
  $mass = 1.63; $length = 4.73; $width = 1.85; $height = 1.46
  $ix = $mass / 12 * ($width * $width + $height * $height)
  $iy = $mass / 12 * ($length * $length + $height * $height)
  $iz = $mass / 12 * ($length * $length + $width * $width)
  $fields = @(544, $mass), @(548, $length), @(552, $width), @(556, $height), @(560, $ix), @(580, $iy), @(600, $iz)
  foreach ($item in $fields) {
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]$item[1]), 0, $D, $F + [int]$item[0], 4)
  }
  [System.IO.File]::WriteAllBytes($Dst, $D)
  [Environment]::Exit(0)
} catch {
  [Console]::Error.WriteLine($_.Exception.Message)
  [Environment]::Exit(1)
}
