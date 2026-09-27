# Ford Fusion Titanium 2018 AWD — Need for Speed Underground 2

Substitui o **Ford Focus** (slot `FOCUS`). O modelo vem do port aprovado de Most Wanted 2005
(`fusion-mw2005`, V1prime-z10); os arquivos de lá não foram alterados. O doador de estrutura é o
**Escort RS** (`source/Ford-Focus-ESCORT-RS`), o mod sedã que já funciona neste jogo.

> **Estado:** finalizado e aprovado no jogo em 27/09/2026. A v9 desenha o carro completo no slot FOCUS (pintura LOD B + LOD A nas áreas que deformavam, sem o emblema do bico, UV de vinil no molde do Focus) com o GlobalB de performance (248 cv, tração integral, chassi do Lancer). O histórico das versões está em [TODO.md](TODO.md).

## No jogo

| Garagem | Cidade |
| --- | --- |
| ![Garagem](docs/in-game-final/final-garagem.png) | ![Frente na cidade](docs/in-game-final/final-cidade-frente.png) |
| ![Traseira na cidade](docs/in-game-final/final-cidade-traseira.png) | ![Largada em Bayview](docs/in-game-final/final-largada.png) |

![Detalhe da frente, com faróis acesos](docs/in-game-final/final-frente.png)

## O que entra no jogo

| Arquivo | Conteúdo |
| --- | --- |
| `CARS/FOCUS/GEOMETRY.BIN` | peças que o slot FOCUS desenha: `KIT00_BODY_A`, `KITW01–04_BODY_A`, `KIT00_TRUNK_A`, `BASE_A`, `KIT00_FRONT_WHEEL_A` e os adesivos |
| `CARS/FOCUS/TEXTURES.BIN` | 15 texturas sem compressão (RAWW). Opacas em DXT1; lentes, sombras e neon em DXT3 |
| `GLOBAL/GlobalB.lzc` | registro `FOCUS` alterado (rodas, massa, inércia, motor, câmbio, tração, chassi). Editado no próprio arquivo do jogo |

`VINYLS.BIN` e `PARTS_ANIMATIONS.bin` continuam os do jogo.

### Peças

| Peça UG2 | Origem (MW z10) | Triângulos |
| --- | --- | --- |
| `KIT00_BODY_A` e `KITW01–04` | pintura LOD B nas áreas planas + LOD A no bico, na frente do teto e no para-choque traseiro. As cinco carrocerias são a mesma malha | 21.228 |
| `KIT00_TRUNK_A` | tampa do porta-malas em LOD A, com a lanterna central | 18.021 |
| `BASE_A` | base, capô LOD B (só a face de cima), bico e frente do teto em LOD A, vidros, faróis, lanternas, interior e motorista | 21.255 |
| `KIT00_FRONT_WHEEL_A` | roda de 20 raios, aro 18" (LOD B) | 8.614 |

Cada peça fica em até 21.500 triângulos (64.500 índices). A v1, com até 62.886 índices concentrados, fechou o jogo.

## Aprendizados aplicados (do MW2005 e deste port)

1. **Limite de índices por peça.** O UG2 fecha o jogo quando uma peça passa de 65.535 índices
   (~21.800 triângulos). O LOD A do Fusion tem ~190 mil triângulos, e o slot FOCUS só desenha
   carroceria, base, porta-malas, roda e adesivos. A pintura foi repartida nessas peças
   (≤ 21.500 triângulos), sem truncar a malha:
   - áreas planas ficam no LOD B; o bico, a frente do teto e o para-choque traseiro usam o LOD A,
     com corte exato (`scripts/clip.py`). Decimar o LOD B por QEM deformava o encontro para-lama/porta;
   - os vidros são uma lâmina nova por janela (`scripts/newglass.py`); o interior foi reduzido para
     caber o LOD A na base.
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

- **Motor e câmbio do Toyota Corolla levados a 248 cv** (o 2.0 EcoBoost do Fusion Titanium 2018): todas as
  curvas de torque (estoque, turbo e upgrades) ×2,212; giro e relações do Corolla. Pela curva: 248 cv
  (245 hp) a 6.560 rpm e 288 Nm (Corolla ~111 hp / 130 Nm; Focus original ~125 hp / 182 Nm).
- **Tração integral**: divisão de torque 0,5 (valor do Lancer Evo VIII), no estoque e nos 3 níveis.
- **Dirigibilidade do Lancer Evo VIII**: pneus, suspensão, direção, freios e tabelas de upgrade;
  massa 1,63 t (Focus 1,15 t, Corolla 0,97 t, Lancer 1,40 t).
- Altura da roda (Z 0,0975), raio 0,3075 e largura 0,195 continuam os do Escort, aprovados no jogo.
- **Carro longo**: dimensões 4,73 × 1,85 × 1,46 m e inércia recalculada a partir delas
  (guinada 3,01 contra 2,67 do Evo), além do entre-eixos de 2,74 m (o Focus tinha 2,54 m).

Valores finais em `docs/globalb_focus.json`.

## Instalação

Na cópia de desenvolvimento já está instalado. Para instalar em outra cópia do jogo: feche o jogo, copie `CARS/FOCUS` e rode
`scripts/globalb_patch.py GlobalB.lzc GlobalB.lzc.novo` sobre o `GLOBAL/GlobalB.lzc` descompactado.
O backup do estado anterior (Escort RS + GlobalB) está em `backup/antes-fusion-2026-09-25`
(fora do git).

| Arquivo instalado | SHA-256 |
| --- | --- |
| `CARS/FOCUS/GEOMETRY.BIN` | `4E731163C867DE8E8787F7C0ED0F624130818FD95A2DA5B72080EDAEB472C2CB` |
| `CARS/FOCUS/TEXTURES.BIN` | `830FD72B7A4A1BAFC061FAABF5AC843722C62C81CB6AF5D4594C94839646457F` |
| `GLOBAL/GlobalB.lzc` | `689B5935A0E1D8C89F3CFB3959F1FF2E4742760AA31E56CB8AC249A7DB9B2462` (rodas + performance; o anterior, só com as rodas, está em `backup/v9-antes-performance/`) |

## Reconstruir

Python 3 + numpy + Pillow. A partir de uma pasta com `mw/` (ZIP da release do MW) e `escort/`
(conteúdo de `FOCUS.7z`, extraível com `scripts/sevenz.py`):

```
python extract_mw.py          # lê o GEOMETRY/TEXTURES do MW -> mw_parts.pkl e texdump/
python build.py out           # GEOMETRY.BIN + TEXTURES.BIN
python globalb_patch.py GlobalB.lzc out/GlobalB.lzc
python preview.py out/GEOMETRY.BIN out/TEXTURES.BIN previa.png
```

![prévia offline](docs/previa-fusion-ug2.png)

O leitor/escritor de GEOMETRY foi validado reescrevendo o Escort RS: estrutura idêntica chunk a chunk.
O compressor JDLZ foi validado com ida e volta contra o descompressor que lê os blobs do Escort.

## Limites conhecidos

Aprovado na garagem, no modo exploração e na largada: carroceria completa (teto, portas e capô), faróis, lanternas e rodas dentro dos arcos.

- Freios (`KIT00_FRONT/REAR_BRAKE_A`) não entram.
- Na tela de som o jogo anima a `TRUNK_A` com o pivô do Focus.
- Logo da tela de seleção (`FrontB.lzc`) e o nome no menu continuam os do Escort/Focus.
- O `VINYLS.BIN` do slot continua o do Focus; a pintura usa a UV projetada no molde dele.
