"""Package both vehicles under one public vX.X release, with byte-level manifests."""
import hashlib
from pathlib import Path
import re
import sys
import zipfile

version, output = sys.argv[1:]
if not re.fullmatch(r'v\d+\.\d+', version):
    raise SystemExit('Use vX.X, for example v1.1.')
root = Path(__file__).resolve().parents[1]
out = Path(output).resolve()
out.mkdir(parents=True, exist_ok=True)
vehicles = [('2018', 'AWD', 'MUSTANGGT', 'Ford Mustang GT'),
            ('2012', 'FWD', 'FOCUS', 'Ford Focus')]
assets = []
content_hashes = []
for year, drive, slot, replaces in vehicles:
    status = ('Base v10.9 aprovada no jogo; extensão do friso e branco inferior da v10.10 aguardam confirmação visual.'
              if year == '2018' else 'Port de desenvolvimento: a exibição das luzes no jogo continua pendente de correção/validação.')
    readme = f'''Ford Fusion Titanium {year} {drive} — NFS Underground 2 — {version}

Substitui: {replaces} ({slot}).
Extraia este ZIP em uma pasta e execute instalar.bat com o jogo fechado.
Confirme a pasta do jogo. O instalador copia o carro e ajusta o GlobalB local;
aceita GlobalB original JDLZ ou descompactado e preserva backup antes-fusion.
Os dois veículos podem ser instalados, cada um a partir do seu ZIP.
Não precisa instalar Python ou descompactar o banco no Nikki.
Mantenha globalb_patch.ps1 ao lado de instalar.bat.

Estado: {status}
A release não inclui GlobalB ou arquivo de idioma completo da instalação local.
Para desfazer: restaure os BIN .antes-fusion e GLOBAL/GlobalB.lzc.antes-fusion.
O backup inicial do GlobalB é compartilhado pelos dois instaladores.

Código, aprendizados e prévias:
https://github.com/nillander/Ford-Fusion-Titanium-NFSU2
'''.encode('utf-8')
    files = {f'CARS/{slot}/{name}': (root / 'CARS' / slot / name).read_bytes()
             for name in ('GEOMETRY.BIN', 'TEXTURES.BIN')}
    for name in ('instalar.bat', 'globalb_patch.ps1'):
        files[name] = (root / 'release' / name).read_bytes()
    files['LEIA-ME.txt'] = readme
    manifest = ''.join(f'{hashlib.sha256(data).hexdigest()}  {name}\n' for name, data in files.items())
    files['SHA256SUMS-conteudo.txt'] = manifest.encode('ascii')
    name = f'Fusion{year}_{drive}_NFSU2.zip'
    with zipfile.ZipFile(out / name, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for entry, data in files.items():
            info = zipfile.ZipInfo(entry, (2026, 10, 6, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
    with zipfile.ZipFile(out / name) as archive:
        assert archive.testzip() is None
        for entry, data in files.items():
            assert archive.read(entry) == data, entry
    assets.append(name)
    content_hashes.append(f'[{name}]\n{manifest}')
for name in ('instalar.bat', 'globalb_patch.ps1'):
    (out / name).write_bytes((root / 'release' / name).read_bytes())
    assets.append(name)
(out / 'SHA256SUMS.txt').write_text(''.join(
    f'{hashlib.sha256((out / name).read_bytes()).hexdigest()}  {name}\n' for name in assets), encoding='ascii')
(out / 'SHA256SUMS-conteudo.txt').write_text('\n'.join(content_hashes), encoding='ascii')
print('\n'.join(assets + ['SHA256SUMS.txt', 'SHA256SUMS-conteudo.txt']))
