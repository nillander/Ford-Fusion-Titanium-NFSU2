# Ford Fusion Titanium 2018 AWD — Need for Speed Underground 2

Substitui o **Ford Focus** (slot `FOCUS`). O modelo vem do port aprovado de Most Wanted 2005
(`fusion-mw2005`, V1prime-z10); os arquivos de lá não foram alterados. O doador de estrutura é o
**Escort RS** (`source/Ford-Focus-ESCORT-RS`), o mod sedã que já funciona neste jogo.

> **Estado:** a v1 fechou o jogo ao selecionar o carro. A v2 (peças ≤ 46.500 índices e sólidos em ordem de hash) está instalada e aguarda teste. Detalhes e plano de bisseção em [CONTINUACAO.md](CONTINUACAO.md).

![prévia](docs/previa-fusion-ug2.png)

## O que entra no jogo

| Arquivo | Conteúdo |
| --- | --- |
| `CARS/FOCUS/GEOMETRY.BIN` | 7 peças no layout do Escort RS (compilador nfsu360): `KIT00_BODY_A`, `KITW01–04_BODY_A`, `BASE_A`, `KIT00_FRONT_WHEEL_A` |
| `CARS/FOCUS/TEXTURES.BIN` | 15 texturas (JDLZ, como o Escort). Opacas em DXT1; só as lentes de farol/lanterna em DXT3 |
| `GLOBAL/GlobalB.lzc` | registro `FOCUS` alterado (rodas, massa, inércia, motor, câmbio, tração, chassi). Editado no próprio arquivo do jogo |

`VINYLS.BIN` e `PARTS_ANIMATIONS.bin` continuam os do jogo.

### Peças

| Peça UG2 | Origem (MW z10) | Triângulos |
| --- | --- | --- |
| `KIT00_BODY_A` (padrão) e `KITW03` | carroceria LOD C + capô LOD C (14.000) + vidros (1.500) | 15.500 |
| `KITW01` ("Street": lábio, saias, lábio traseiro) e `KITW04` | KIT01 LOD C + capô + vidros | 15.500 |
| `KITW02` ("Race": splitter, saias, difusor) | KIT02 LOD C + capô + vidros | 15.499 |
| `BASE_A` | base LOD C (grade, frisos, chassi, placas, emblemas) + interior + motorista + faróis e lanternas (LOD C) | 15.435 |
| `KIT00_FRONT_WHEEL_A` | roda de 20 raios aro 18" (LOD B) | 8.614 |

Todas com no máximo 46.500 índices e 19 mil vértices por peça (a v1, com até 62.886 índices, fechou o jogo).

## Aprendizados aplicados (do MW2005 e deste port)

1. **Limite de índices por peça.** O UG2 fecha o jogo quando uma peça passa de 65.535 índices
   (~21.800 triângulos). O LOD A do Fusion tem ~190 mil triângulos. O port anterior *truncava* as
   malhas; aqui a malha não é cortada:
   - carroceria e base usam o **LOD C autoral do GTA V** (liso, sem facetas); decimar o LOD B por
     QEM deformava o encontro para-lama/porta (as "manchas" do MW voltavam);
   - vidros (12 mil → 2.300) e interior (18,5 mil → 7.600) passam por decimação que preserva
     costuras de UV, bordas e troca de material (`scripts/decimate.py`), com normais recalculadas.
2. **DXT1 para peças opacas.** DXT3 desliga a gravação de profundidade (lição da grade do MW).
   MISC, LOGO, INTERIOR, BADGING, roda, pneu, motorista e as carcaças dos faróis/lanternas são DXT1.
   As lentes usam uma cópia DXT3 separada da mesma folha e ficam por último na ordem de desenho.
3. **Kits não podem sumir com o carro.** As 4 carrocerias `KITW` existem (carros da IA aplicam
   kits aleatórios).
4. **Rodas pela geometria, não por chute.** Os arcos dos para-lamas foram medidos na malha:
   dianteira X = +1,431, traseira X = −1,311 (entre-eixos 2,74 m), Y = ±0,78, Z = 0,13,
   raio 0,3225 (235/40 R18), largura 0,235. O port anterior gravava 3,3 m de entre-eixos.
5. **Marcadores** (faróis, lanternas, brake light central, escapamentos, aerofólio, entrada de ar do
   teto) vêm das posições aprovadas no MW; no UG2 o lado esquerdo é +Y.

## Performance (`scripts/globalb_patch.py`)

- **Motor e câmbio do Toyota Corolla** (curvas de torque, turbo, giro, relações; estoque e upgrades).
- **Tração integral**: divisão de torque 0,5 (valor do Lancer Evo VIII), no estoque e nos 3 níveis.
- **Dirigibilidade do Lancer Evo VIII**: pneus, suspensão, direção, freios e tabelas de upgrade;
  massa 1,40 t.
- **Carro longo**: dimensões 4,73 × 1,85 × 1,46 m e inércia recalculada a partir delas
  (guinada 3,01 contra 2,67 do Evo), além do entre-eixos de 2,74 m (o Focus tinha 2,54 m).

Valores finais em `docs/globalb_focus.json`.

## Instalação

Já está instalado. Para reinstalar em outra cópia do jogo: feche o jogo, copie `CARS/FOCUS` e rode
`scripts/globalb_patch.py GlobalB.lzc GlobalB.lzc.novo` sobre o `GLOBAL/GlobalB.lzc` descompactado.
O backup do estado anterior (Escort RS + GlobalB) está em `backup/antes-fusion-2026-09-25`
(fora do git).

| Arquivo instalado | SHA-256 |
| --- | --- |
| `CARS/FOCUS/GEOMETRY.BIN` | `54AB592EF1262099DD2D9E3B32719B0405A0E0509805F868A09D09AB7EB0A5E1` |
| `CARS/FOCUS/TEXTURES.BIN` | `5C2D9E1D7BCDBC61FA650665291C9607651B8CF747295189A46A171416068C10` |
| `GLOBAL/GlobalB.lzc` | `1A4537153D0B89FE9B3FA37AC7B5B6A79CB3993C9E17A7C6196EED5290C65A9C` |

## Reconstruir

Python 3 + numpy + Pillow. A partir de uma pasta com `mw/` (ZIP da release do MW) e `escort/`
(conteúdo de `FOCUS.7z`, extraível com `scripts/sevenz.py`):

```
python extract_mw.py          # lê o GEOMETRY/TEXTURES do MW -> mw_parts.pkl e texdump/
python build.py out           # GEOMETRY.BIN + TEXTURES.BIN
python globalb_patch.py GlobalB.lzc out/GlobalB.lzc
python preview.py out/GEOMETRY.BIN out/TEXTURES.BIN previa.png
```

O leitor/escritor de GEOMETRY foi validado reescrevendo o Escort RS: estrutura idêntica chunk a chunk.
O compressor JDLZ foi validado com ida e volta contra o descompressor que lê os blobs do Escort.

## Limites conhecidos / não testado

- Não foi aberto no jogo. Pontos a conferir: rodas dentro dos arcos (se ficarem para fora/dentro,
  ajuste Y no Nikki), sombra, brilho de faróis/lanternas.
- Freios e porta-malas (`TRUNK_A`) não entram (o Escort também não tem).
- Logo da tela de seleção (`FrontB.lzc`) e nome no menu continuam os do Escort/Focus.
- Adesivos: o `VINYLS.BIN` do slot foi feito para a UV do Focus; o mapa da pintura é o do MW.
