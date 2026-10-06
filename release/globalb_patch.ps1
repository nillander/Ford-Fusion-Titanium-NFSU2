param([string]$InputPath=$env:FUSION_IN, [string]$OutputPath=$env:FUSION_OUT, [ValidateSet("MUSTANGGT","FOCUS")][string]$Slot=$env:FUSION_SLOT)
$ErrorActionPreference = 'Stop'
function Expand-Jdlz([byte[]]$blob) {
  $length = [BitConverter]::ToInt32($blob,8)
  if ($length -le 0 -or $length -gt 268435456) { throw 'Tamanho JDLZ invalido.' }
  $out = New-Object byte[] $length
  $ip=16; $op=0; $f1=1; $f2=1
  while ($op -lt $length) {
    if ($f1 -eq 1) { $f1 = [int]$blob[$ip] -bor 256; $ip++ }
    if ($f2 -eq 1) { $f2 = [int]$blob[$ip] -bor 256; $ip++ }
    if ($f1 -band 1) {
      if ($f2 -band 1) {
        $n = ([int]$blob[$ip+1] -bor (([int]$blob[$ip] -band 240) -shl 4)) + 3
        $back = ([int]$blob[$ip] -band 15) + 1
      } else {
        $n = ([int]$blob[$ip] -band 31) + 3
        $back = ([int]$blob[$ip+1] -bor (([int]$blob[$ip] -band 224) -shl 3)) + 17
      }
      $ip+=2
      if ($back -gt $op -or $op+$n -gt $length) { throw 'Referencia JDLZ invalida.' }
      for ($j=0; $j -lt $n; $j++) { $out[$op+$j]=$out[$op+$j-$back] }
      $op+=$n; $f2=$f2 -shr 1
    } else { $out[$op]=$blob[$ip]; $op++; $ip++ }
    $f1=$f1 -shr 1
    if ($ip -gt $blob.Length) { throw 'JDLZ truncado.' }
  }
  return ,$out
}
function Name-Hash([string]$name) {
  [uint64]$h=4294967295
  foreach ($c in [Text.Encoding]::ASCII.GetBytes($name)) { $h=($h*33+$c) -band [uint64]4294967295 }
  return [uint32]$h
}
function Set-SelectiveParts([byte[]]$data, $chunk) {
  if ($null -eq $chunk) { throw 'Banco de pecas ausente.' }
  $subs=@{}; $q=$chunk[0]+8; $end=$q+$chunk[1]
  while ($q+8 -le $end) {
    $cid=[BitConverter]::ToUInt32($data,$q); $sz=[BitConverter]::ToInt32($data,$q+4)
    $subs[$cid]=@(($q+8),$sz); $q+=8+$sz
  }
  $packs=$subs[[uint32]0x3460B]; $rows=$subs[[uint32]0x34604]
  if ($null -eq $packs -or $null -eq $rows) { throw 'Tabelas de pecas ausentes.' }
  $focus=-1; $mustang=-1
  for ($i=0; $i -lt $packs[1]/4; $i++) {
    $h=[BitConverter]::ToUInt32($data,$packs[0]+4*$i)
    if ($h -eq (Name-Hash 'FOCUS')) { $focus=$i }
    if ($h -eq (Name-Hash 'MUSTANGGT')) { $mustang=$i }
  }
  if ($focus -lt 0 -or $mustang -lt 0) { throw 'Slots de pecas ausentes.' }
  $donor=@{}
  for ($r=$rows[0]; $r+14 -le $rows[0]+$rows[1]; $r+=14) {
    if ($data[$r+7] -eq $focus) { $donor[[int]$data[$r+4]*256+$data[$r+5]]=$r }
  }
  $updated=0
  for ($r=$rows[0]; $r+14 -le $rows[0]+$rows[1]; $r+=14) {
    if ($data[$r+7] -ne $mustang -or $data[$r+4] -notin @(5,6,10,28)) { continue }
    $key=[int]$data[$r+4]*256+$data[$r+5]
    if (-not $donor.ContainsKey($key)) { throw 'Peca do Focus ausente.' }
    [Buffer]::BlockCopy($data,$donor[$key]+12,$data,$r+12,2); $updated++
  }
  if ($updated -eq 0) { throw 'Nenhuma peca do Mustang encontrada.' }
}
try {
  $Src = $InputPath
  $Dst = $OutputPath
  $REC = 2192
  $D = [System.IO.File]::ReadAllBytes($Src)
  if ([Text.Encoding]::ASCII.GetString($D,0,4) -eq 'JDLZ') { $D = Expand-Jdlz $D }
  $script:partChunk = $null
  $found = New-Object System.Collections.Generic.List[object]
  function Walk([int]$start, [int]$end) {
    $p = $start
    while (($p + 8) -le $end) {
      $cid = [BitConverter]::ToUInt32($D, $p)
      $sz = [BitConverter]::ToInt32($D, $p + 4)
      if ($cid -eq 2147698178 -and $null -eq $script:partChunk) { $script:partChunk = @($p, $sz) }
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
  foreach ($need in @($Slot,'COROLLA','LANCEREVO8')) {
    if (-not $recs.ContainsKey($need)) { throw "Registro $need ausente no GlobalB." }
  }
  $F = $recs[$Slot]; $C = $recs['COROLLA']; $L = $recs['LANCEREVO8']
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
  foreach ($o in @(720,1136,1200,1264)) {
    if ($Slot -eq "FOCUS") { [Buffer]::BlockCopy([BitConverter]::GetBytes([single]0),0,$D,$F+$o,4) }
    else { Copy-Range $L $o ($o + 4) }
  }
  $wheels = @(@(1.431,0.78), @(1.431,-0.78), @(-1.311,-0.78), @(-1.311,0.78))
  for ($i = 0; $i -lt 4; $i++) {
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]$wheels[$i][0]), 0, $D, $F + 288 + 48 * $i, 4)
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]$wheels[$i][1]), 0, $D, $F + 288 + 48 * $i + 4, 4)
    # Z, raio e largura aprovados no jogo (o registro do Mustang vem com Z 0,17 e raio 0,343)
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]0.09754), 0, $D, $F + 288 + 48 * $i + 8, 4)
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]0.3075), 0, $D, $F + 288 + 48 * $i + 16, 4)
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]0.195), 0, $D, $F + 288 + 48 * $i + 20, 4)
  }
  $mass = 1.63; $length = 4.73; $width = 1.85; $height = 1.46
  $ix = $mass / 12 * ($width * $width + $height * $height)
  $iy = $mass / 12 * ($length * $length + $height * $height)
  $iz = $mass / 12 * ($length * $length + $width * $width)
  $fields = @(544, $mass), @(548, $length), @(552, $width), @(556, $height), @(560, $ix), @(580, $iy), @(600, $iz)
  foreach ($item in $fields) {
    [Buffer]::BlockCopy([BitConverter]::GetBytes([single]$item[1]), 0, $D, $F + [int]$item[0], 4)
  }
  if ($Slot -eq "MUSTANGGT") { Set-SelectiveParts $D $script:partChunk }
  [System.IO.File]::WriteAllBytes($Dst, $D)
  [Environment]::Exit(0)
} catch {
  [Console]::Error.WriteLine($_.Exception.Message)
  [Environment]::Exit(1)
}
