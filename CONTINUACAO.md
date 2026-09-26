# Continuação — Fusion Titanium 2018 AWD no NFSU2 (slot FOCUS)

Documento para retomar o trabalho em outra sessão. Atualizado em 26/09/2026.

## 1. Pedido

- Construir um Ford Fusion Titanium 2018 AWD para o NFS Underground 2, instalado **sobre o Ford Focus**,
  usando o aprendizado do port aprovado do MW2005 (`C:\Users\nillander\NoDocuments\fusion-mw2005`,
  versão V1prime-z10). Os arquivos do MW2005 não podem ser alterados.
- Doador de estrutura: `source/Ford-Focus-ESCORT-RS` (sedã que já funciona no jogo).
- Performance: **potência do Corolla + tração integral + dirigibilidade do Lancer Evo**.
- Instalar direto no jogo com backup; commit **local** (sem push).

## 2. Estado atual

| Versão | O que é | Resultado no jogo |
| --- | --- | --- |
| v1 (commit `28a6a9c`) | peças até 62.886 índices / 24.303 vértices; sólidos gravados fora da ordem de hash | **Fechou o jogo ao selecionar o carro** |
| v2 (instalada agora) | todas as peças ≤ 46.500 índices e ≤ 19.000 vértices; sólidos gravados em ordem de hash como o nfsu360 | **aguardando teste** |

SHA-256 da v2: GEOMETRY `54AB592E…A5E1`, TEXTURES `5C2D9E1D…0C10` (igual à v1), GlobalB `1A453715…5A9C` (igual à v1).

### Hipóteses para o fechamento da v1 (em ordem de probabilidade)

1. **Tamanho da peça.** O port antigo do Cursor também fechava na ficha do carro e só parou ao limitar
   cada peça a 60.000 índices. A `BASE_A` da v1 tinha 62.886. Os mods que funcionam ficam em
   41–52 mil índices (Senna tem uma peça com 61.458) e no máximo 17.702 vértices por peça.
   → v2 reduz tudo para ≤ 46.500 índices e ≤ 19 mil vértices.
2. **Ordem dos sólidos no arquivo.** Todos os mods que funcionam (Escort, Focus RS, Senna, F-150) gravam os
   sólidos ordenados pelo hash do nome, na mesma ordem da tabela `0x134004`. A v1 gravava em outra ordem.
   → v2 corrigido (`ug2write.py` ordena).
3. **TEXTURES.BIN** (compressor JDLZ próprio). Ida e volta confere com o descompressor que lê os blobs
   do Escort, mas nunca foi lido pelo jogo. Não mudou na v2.
4. **GlobalB** (registro FOCUS). Só números copiados de Corolla/Lancer + rodas/massa/inércia. Pouco provável.

### Se a v2 também fechar — bisseção (um teste por vez, jogo fechado)

1. Voltar só o `GLOBAL/GlobalB.lzc` do backup e manter a v2 → se abrir, o culpado é o GlobalB.
2. Com o GlobalB do backup: `CARS/FOCUS/TEXTURES.BIN` do Escort (backup) + GEOMETRY v2 → se abrir
   (carro sem textura), o culpado é o TPK/JDLZ.
3. Se ainda fechar, é a GEOMETRY: gerar uma versão só com `KIT00_BODY_A` + `BASE_A` do Escort trocando
   uma peça por vez pela do Fusion.

Backup do estado anterior ao Fusion (Escort RS + GlobalB do usuário):
`fusion-nfsu2/backup/antes-fusion-2026-09-25` (fora do git; tem `SHA256SUMS.txt`).

## 3. O que foi descoberto sobre os formatos

### GEOMETRY.BIN do UG2 (layout nfsu360)

- Raiz `0x80134000` → chunk vazio → `0x80134001` { `0x134002` (144 bytes: 8 zeros, `0x1D`, nº de peças,
  "NFS:U2 Geometry Compiler by nfsu360" em 0x38, "DEFAULT" em 0x20, `0x80`), `0x134003` (hash,0),
  `0x134004` (hash, offset absoluto, tamanho, tamanho, 0, 0), `0x80134008` vazio }.
- Antes de cada sólido um chunk `0x0` de preenchimento para alinhar em 0x80 (sempre, mesmo alinhado),
  e um no fim do arquivo.
- Sólido `0x80134010`: `0x134011` cabeçalho (12 zeros, versão 0x16, flags 0x40, hash, NumPolys u16,
  NumVerts u16 = 0, bytes [0, nTex, nLuz, 0], bounds, matriz identidade, 8 zeros, `0xEE580` ×2, 0,
  1.0f, NumPolys como float, 0, 0, **nome em 28 bytes fixos**), `0x134012` texturas (hash,0),
  `0x134013` materiais de luz (hash,0), `0x13401A` marcadores (80 bytes: hash, 3 zeros, matriz 4×4),
  `0x80134100` { `0x134900` (68 bytes: 8 zeros, 0x10, 0x4180, nGrupos, 4 zeros, nTris, 3 zeros,
  nVerts, 3 zeros), `0x134B01` vértices alinhados em 0x80 (36 bytes: pos, normal, cor u32, uv),
  `0x134B02` grupos de 60 bytes (bounds ±5000, nº de índices, idx textura, idx material, 4 zeros,
  offset em índices, flags 0x4180), `0x134B03` índices u16 **globais** do sólido }.
- `scripts/ug2write.py` reescreve o Escort com a mesma estrutura chunk a chunk (só bounds e bytes de
  preenchimento diferem).
- Peças usadas pelo Escort e pelo Fusion: `KIT00_BODY_A`, `KITW01–04_BODY_A`, `BASE_A`,
  `KIT00_FRONT_WHEEL_A` (o Escort ainda tem `KIT00_TRUNK_A`).
- Hash = `h = 0xFFFFFFFF; h = h*33 + c` (`scripts/hashes.py`).

### TEXTURES.BIN do UG2

- Raiz `0xB3300000` → `0x0` (48) → `0xB3310000` { `0x33310001` (versão 5, caminho "NFS:U2/MW Texture
  Compiler by nfsu360"), `0x33310002` hashes, `0x33310003` (hash, offset absoluto, tamanho comprimido,
  tamanho, 0x100, 0) } → `0x0` até 0x80 → blobs JDLZ em sequência.
- Blob descomprimido = dados + (cauda) + info de 124 bytes + 32 bytes DDS. `ImagePlacement` é cumulativo
  na ordem de hash. Byte 74: 0x22 = DXT1, 0x24 = DXT3. DXT1 opaca usa classe `1B81E7B0`; DXT3 `001A93CF`
  com flags de alfa.
- JDLZ: `scripts/jdlz.py` (compressor) e `scripts/tpk2.py` (descompressor, confere com os blobs do Escort).
  Retail usa HUFF (não implementado).

### Texturas e materiais globais

- Pintura: textura global `3C84D757` + material `CARSKIN`. Vidro: textura `WINDOW` + material `WINDSHIELD`.
- Materiais de luz existentes no GlobalB: DULLPLASTIC, INTERIOR, LICENSEPLATE, HEADLIGHTGLASS,
  HEADLIGHTREFLECTOR, BRAKELIGHT, BRAKELIGHTGLASS, DRIVER, RUBBER, USER_RIMS, CHROME, METPAINTBLACK…

### GlobalB.lzc — registro CarTypeInfo (chunk `0x34600`, 2.192 bytes por carro)

- O `GlobalB.lzc` do jogo está **descomprimido** (salvo pelo Nikki); o original em `_backup-ptbr` é JDLZ.
- Offsets no registro: 220 bytes de aro (externo, mín, máx); 288 + 48·i = roda i (x, y, z, 0, raio,
  largura, índice, 2 valores); ordem FL(+y), FR(−y), RR(−y), RL(+y); **+y é o lado esquerdo**;
  544 massa (t), 548–556 comprimento/largura/altura, 560/580/600 inércias (m/12·(a²+b²));
  704–880 câmbio/motor/turbo de estoque (720 = divisão de torque para trás: FWD 0, RWD 1, AWD 0,5;
  736 ré, 744+ marchas, 768 marcha lenta, 772 corte, 776 rpm máx, 784–816 curva de torque);
  992–1616 tabelas de upgrade de motor/câmbio (divisão de torque também em 1136/1200/1264);
  480–704, 880–992, 1616–2032 pneus/suspensão/direção/freios (e upgrades).
- `scripts/globalb_patch.py` aplica: motor/câmbio do COROLLA, chassi do LANCEREVO8, torque 0,5,
  rodas do Fusion, dimensões 4,73 × 1,85 × 1,46, massa 1,40 t e inércia recalculada.

## 4. Geometria do Fusion (medida na malha do MW)

- Arcos: roda dianteira X = +1,431, traseira X = −1,311 (entre-eixos 2,74 m); para-lama em |y| = 0,91.
- Rodas gravadas: Y = ±0,78, Z = 0,13, raio 0,3225, largura 0,235 (Y foi estimado comparando com o
  Escort/Corolla — conferir no jogo).
- Marcadores do MW (esquerda/direita trocados para o UG2): faróis (2,15; ±0,577; 0,515), lanternas
  (−2,22; ±0,653; 0,688), escapamentos nos corpos (−2,32; ±0,635; 0,135), brake light central,
  aerofólio (−2,15; 0; 0,868), entrada de ar do teto (0,3; 0; 1,207).

## 5. Montagem (v2)

| Peça | Conteúdo | Tris / vértices |
| --- | --- | --- |
| `KIT00_BODY_A`, `KITW03` | pintura KIT00 LOD C + capô C (decimada para 14.000) + vidros (1.500) | 15.500 / 18.710 |
| `KITW01`, `KITW04` | kit "Street" (KIT01 C) | 15.500 / 18.724 |
| `KITW02` | kit "Race" (KIT02 C) | 15.499 / 18.741 |
| `BASE_A` | base C (MISC/LOGO −15 %) + interior (5.834) + motorista (1.000) + faróis/lanternas LOD C | 15.435 / 18.967 |
| `KIT00_FRONT_WHEEL_A` | roda 20 raios LOD B | 8.614 / 5.386 |

- Lição: decimar o LOD A/B por QEM deformava a junção para-lama/porta; o **LOD C do GTA** fica liso.
  Só vale decimar pouco (≤ 15 %) ou peças planas (vidro) e escuras (interior).
- Texturas: MISC, LOGO, INTERIOR, BADGING 512 DXT1; faróis/lanternas 256 DXT1 (carcaça) + 256 DXT3
  (lentes, por último); roda, pneu e motorista 256 DXT1; do Escort ficam SHADOWFE/IG, NEON e `6F62BC7B`.

## 6. Como reconstruir

A área de trabalho na nuvem é temporária. Tudo o que é preciso está em `scripts/`:

1. Pasta de trabalho com `mw/` = ZIP `fusion-mw2005/release/Fusion2018_AWD_MW2005.zip` extraído e
   `escort/` = `FOCUS.7z` extraído (`python sevenz.py`; o header é LZMA puro, sem 7-Zip).
2. `python extract_mw.py` → `mw_parts.pkl` e `texdump/`.
3. `python build.py out` → `out/GEOMETRY.BIN`, `out/TEXTURES.BIN`, `out/build_log.json`.
4. `python globalb_patch.py <GlobalB atual> out/GlobalB.lzc` (sempre sobre o GlobalB **atual** do jogo:
   o usuário edita com o Nikki).
5. `python preview.py out/GEOMETRY.BIN out/TEXTURES.BIN previa.png` (lê de volta o binário).
6. Instalar com o jogo fechado e conferir SHA-256.

Ferramentas indisponíveis no ambiente: pip/npm/apt bloqueados (sem py7zr, trimesh etc.). Por isso há
decimador, codificador DXT, JDLZ e extrator 7z próprios em Python/numpy.

## 7. Pendências

- [ ] Testar a v2 no jogo (seleção do carro, garagem, corrida).
- [ ] Se abrir: conferir posição lateral das rodas (Y), sombra, brilho de faróis/lanternas, kits.
- [ ] Logo da tela de seleção (`FrontB.lzc`) e nome no menu (LANGUAGES) ainda são do Escort/Focus.
- [ ] Freios (`KIT00_FRONT/REAR_BRAKE_A`) e porta-malas não incluídos.
- [ ] VINYLS.BIN do slot é o do Focus; UV da pintura é a do MW.
