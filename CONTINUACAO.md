# Continuação — Fusion Titanium 2018 AWD no NFSU2 (slot FOCUS)

Documento para retomar o trabalho em outra sessão. Atualizado em 26/09/2026 (v4). O estado mais recente e a lista de pendências estão em [TODO.md](TODO.md).

> O port foi **finalizado e aprovado no jogo** em 27/09/2026. Este arquivo guarda o diário até a v4. O resultado está no [README.md](README.md).

## 1. Pedido

- Construir um Ford Fusion Titanium 2018 AWD para o NFS Underground 2, instalado **sobre o Ford Focus**,
  usando o aprendizado do port aprovado do MW2005 (`C:\Users\nillander\NoDocuments\fusion-mw2005`,
  versão V1prime-z10). Os arquivos do MW2005 não podem ser alterados.
- Doador de estrutura: `source/Ford-Focus-ESCORT-RS` (sedã que já funciona no jogo).
- Performance: **potência do Corolla + tração integral + dirigibilidade do Lancer Evo**.
- Instalar direto no jogo com backup; commit **local** (sem push).

## 2. Estado atual

| Versão | O que muda | Resultado no jogo |
| --- | --- | --- |
| v1 (`28a6a9c`) | peças até 62.886 índices / 24.303 vértices; sólidos fora da ordem de hash; TPK JDLZ; GlobalB com performance | **fechou ao selecionar o carro** |
| v2 (`f3ff5b4`) | peças ≤ 46.500 índices / 19 mil vértices; sólidos em ordem de hash; resto igual à v1 | **fechou ao selecionar o carro** |
| v3 — teste A | GEOMETRY da v2 + **TPK sem compressão (RAWW, layout do mwtc)** + **GlobalB original** (sem performance) | **abriu**, mas com rodas fora do lugar, vidros furados, capô manchado, lanternas sem lente |
| **v4 (instalada)** | pintura LOD B sem decimação + `KIT00_TRUNK_A`; vidros das duas peças do MW só com a camada externa; capô B só com a face de cima; lente da lanterna com `BRAKELIGHT` e dupla face; GlobalB original só com X/Y das rodas; TEXTURES da v3 | aguardando — ver [TODO.md](TODO.md) |

Como a v2 também fechou, o tamanho das peças e a ordem dos sólidos não eram (só) o problema. Restam os
dois componentes que a v1 e a v2 tinham iguais:

- **TEXTURES.BIN com o compressor JDLZ próprio.** Ele usa cópias longas (até 4.098 bytes) que o
  compilador nfsu360 nunca gera (máximo 710 no Escort) e termina o blob sem o byte extra que o nfsu360
  deixa. O port antigo do Cursor usava o TPK do MW como estava (RAWW, sem compressão).
  → v3 grava RAWW, igual ao `mwtc`.
- **GlobalB** (registro FOCUS). → teste A usa o GlobalB original do backup. Com ele, as rodas ficam nas
  posições do Escort (entre-eixos curto) — é só para ver se o carro carrega.

SHA-256 instalados no teste A: GEOMETRY `54AB592E…A5E1`, TEXTURES `349F6BEC…26B4`,
GlobalB `10A8EAE6…BBB9` (o do backup, sem alteração).
GlobalB com performance (v3, sem mexer nos bytes de aro): `variantes/performance/GlobalB.lzc`
(`F45D3B2D…8926`, fora do git).

### Próximos passos conforme o resultado do teste A

- **Abriu:** copiar `variantes/performance/GlobalB.lzc` para `GLOBAL/` (teste B).
  Se abrir → o culpado era o TPK JDLZ; se fechar → o culpado é o GlobalB: aplicar o patch em partes
  (só rodas; depois chassi do Lancer; depois motor do Corolla) até achar o bloco.
- **Fechou:** o culpado é a GEOMETRY. Montar híbridos a partir do GEOMETRY do Escort trocando uma peça por
  vez pela do Fusion (`BASE_A`, depois `KIT00_BODY_A`, depois a roda), sempre com o GlobalB original.
  Diferenças a investigar: marcadores (matrizes do MW), número de grupos da BASE (13), materiais
  HEADLIGHTREFLECTOR/BRAKELIGHTGLASS/DRIVER/USER_RIMS, vértices com cor/UV do MW.

Híbridos já prontos em `variantes/hibridos/` (usar com `TEXTURES_uniao.BIN`, que tem as texturas do
Escort + as do Fusion, e com o GlobalB original):
`H0_escort_regravado` (Escort passado pelo `ug2write.py` — controle), `H1_base` (Escort com a `BASE_A` do
Fusion), `H2_body` (Escort com o `KIT00_BODY_A` do Fusion), `H3_roda` (Escort com a roda do Fusion).
Gerados por `scripts/hybrids.py`.

Port antigo do Cursor (para comparação): `backup/port-antigo-cursor/` (GEOMETRY de 31 MB com 159 peças,
flags 0x4080, TPK do MW). Não se sabe se ele chegou a exibir o carro.

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
3. `python build.py out` (v4) → `out/GEOMETRY.BIN`, `out/TEXTURES.BIN`, `out/build_log.json`.
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
