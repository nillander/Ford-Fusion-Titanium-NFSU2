# Ford Fusion — Need for Speed Underground 2

Dois ports, a partir dos ZIPs do Most Wanted 2005. Os arquivos de lá não são alterados. A estrutura que o Underground 2 aceita foi medida no **Escort RS**.

| Most Wanted | Underground 2 | Carro |
| --- | --- | --- |
| `MUSTANGGT` | `MUSTANGGT` | Fusion Titanium 2018 AWD |
| `COBALTSS` | `FOCUS` | Fusion Titanium 2012 FWD |

O Fusion Titanium 2012 reaproveita o caminho do 2018 (corte, vidros, adesivos, vinil, chassi). O que muda é o slot e a tração, dianteira no 2012. O método está em [docs/PORTAR-PARA-NFSU2.md](docs/PORTAR-PARA-NFSU2.md).

> **Estado:** em 06/10/2026 os dois carros foram reexportados da release **v2.7** do Most Wanted e instalados para teste (v10): o Fusion Titanium 2018 AWD em `CARS/MUSTANGGT`, no lugar do Ford Mustang GT, e o Fusion Titanium 2012 FWD em `CARS/FOCUS`, no lugar do Ford Focus. A v9 do 2018, aprovada no jogo em 27/09/2026 no slot do Focus, é a das capturas abaixo. O histórico está em [TODO.md](TODO.md).

## No jogo

| Garagem | Cidade |
| --- | --- |
| ![Garagem](docs/in-game-final/final-garagem.png) | ![Frente na cidade](docs/in-game-final/final-cidade-frente.png) |
| ![Traseira na cidade](docs/in-game-final/final-cidade-traseira.png) | ![Largada em Bayview](docs/in-game-final/final-largada.png) |

![Detalhe da frente, com faróis acesos](docs/in-game-final/final-frente.png)

## O que entra no jogo

| Arquivo | Conteúdo |
| --- | --- |
| `CARS/MUSTANGGT/GEOMETRY.BIN` | Fusion 2018: `KIT00_BODY_A`, `KITW01–04_BODY_A`, `KIT00_TRUNK_A`, `BASE_A`, `KIT00_FRONT_WHEEL_A` e os adesivos |
| `CARS/MUSTANGGT/TEXTURES.BIN` | 14 texturas sem compressão (RAWW). Opacas em DXT1; lentes, sombras e neon em DXT3 |
| `CARS/FOCUS/GEOMETRY.BIN` | Fusion 2012: as mesmas peças, com prefixo `FOCUS_` |
| `CARS/FOCUS/TEXTURES.BIN` | 15 texturas RAWW. A lente do farol do 2012 tem cópia própria (`FOCUS_HEADLIGHT_LENS`) |
| `GLOBAL/GlobalB.lzc` | registros `MUSTANGGT` e `FOCUS` alterados (rodas, massa, inércia, motor, câmbio, tração, chassi). Editado no próprio arquivo do jogo |

`VINYLS.BIN` e `PARTS_ANIMATIONS.bin` continuam os do jogo.

### Peças

| Peça UG2 | Origem (MW z10) | Triângulos |
| --- | --- | --- |
| `KIT00_BODY_A` e `KITW01–04` | pintura LOD B nas áreas planas + LOD A no bico, na frente do teto e no para-choque traseiro. As cinco carrocerias são a mesma malha | 21.228 |
| `KIT00_TRUNK_A` | tampa do porta-malas em LOD A, com a lanterna central | 18.021 |
| `BASE_A` | base, capô LOD B (só a face de cima), bico e frente do teto em LOD A, vidros, faróis, lanternas, interior e motorista | 21.236 |
| `KIT00_FRONT_WHEEL_A` | roda de 20 raios, aro 18" (LOD B) | 8.614 |

O 2012 tem faróis e lanternas nos dois lados e cerca de 2,5 vezes mais triângulos neles e na traseira, em todos os LODs. Para caber, a distribuição muda (valores em `scripts/ports.py`, explicados em [docs/PORTAR-PARA-NFSU2.md](docs/PORTAR-PARA-NFSU2.md)):

| Peça UG2 (2012) | Conteúdo | Triângulos |
| --- | --- | --- |
| `KIT00_BODY_A` e `KITW01–04` | pintura LOD B, bico e frente do teto em LOD A, faróis LOD D com lente LOD C | 21.392 |
| `KIT00_TRUNK_A` | tampa LOD B, para-choque traseiro LOD B e as lanternas LOD D | 20.636 |
| `BASE_A` | base, peças pintadas da base, capô, vidros, interior e motorista | 21.256 |
| `KIT00_FRONT_WHEEL_A` | a mesma roda do 2018 | 8.614 |

Cada peça fica em até 21.500 triângulos (64.500 índices). A v1, com até 62.886 índices concentrados, fechou o jogo.

### A malha nas imagens

Azul é `KIT00_BODY_A`. Cinza é `BASE_A`: capô, frente do teto, vidros, faróis e lanternas. Laranja é `KIT00_TRUNK_A`. A roda preta está nos quatro arcos medidos na malha. Os quatro `KITW` repetem a malha azul e ficam de fora deste render. A imagem sai do `GEOMETRY.BIN` instalado.

![Peças do GEOMETRY.BIN por cor](docs/geometria/pecas-por-cor.png)

A v9 inteira, nas seis vistas de `scripts/preview.py`. Magenta é face de costas ou a lente; o para-lama por dentro sai verde.

![Seis vistas da geometria aprovada](docs/diagnostico-v8/v9-carro-completo.png)

| Uma lâmina de vidro por janela | Pintura no molde de vinil do Focus |
| --- | --- |
| ![Vidros da v5](docs/diagnostico-v4/v5-vidros-detalhe.png) | ![UV LEFT, TOP e RIGHT no molde do Focus](docs/diagnostico-v8/vinil-molde-focus.png) |

| As cinco carrocerias são a mesma malha | v8: pintura em peças que o slot não desenha |
| --- | --- |
| ![Frente e traseira dos kits](docs/previa-kits.png) | ![Garagem da v8, sem teto, portas e capô](docs/in-game-v8/v8-sem-teto-portas.png) |

### Da v3 à v5

A v3 decimou a pintura. Magenta é face de costas ou buraco: o capô, o teto e a coluna ficaram partidos.

![Faces da v3](docs/diagnostico-v4/v3-faces.png)

A v4 fechou essa lataria e devolveu o vidro traseiro que vinha do Most Wanted. As faixas douradas são o `REAR_WINDOW` de origem. A v5 substituiu o vidro decimado por uma lâmina nova em cada janela.

| Vidro traseiro do MW, com a faixa que faltava | As lâminas da v5, sem a carroceria |
| --- | --- |
| ![Vidro traseiro herdado](docs/diagnostico-v4/mw-rear-window.png) | ![Vidros sozinhos](docs/diagnostico-v4/v5-vidros-sozinhos.png) |

Na v4 o para-lama por dentro já sai verde e o miolo da lataria deixa de ser mancha magenta.

![Faces da v4](docs/diagnostico-v4/v4-faces.png)

### Bico, tampa, adesivos e molde

| Rebaixo do emblema, preenchido na pintura | Tampa e lanternas da malha aprovada |
| --- | --- |
| ![Bico sem o emblema](docs/diagnostico-v8/bico-sem-emblema.png) | ![Traseira da v9](docs/diagnostico-v8/traseira.png) |

| Molde de vinil do Focus, antes de projetar a pintura | Lanternas lidas do Most Wanted |
| --- | --- |
| ![Molde LEFT, TOP e RIGHT](docs/diagnostico-v8/FOCUS_DEBUG-molde.png) | ![Lanternas do MW](docs/diagnostico-v4/mw-lanternas.png) |

As faixas coloridas são as peças `DECAL`, não a pintura. Elas sentam no para-brisa, no capô e nas portas. No centro do para-brisa a v6 ainda mostra a emenda das duas lâminas.

| Adesivos de teste na v6 | Emenda do para-brisa |
| --- | --- |
| ![Adesivos sobre a carroceria](docs/diagnostico-v4/v6-adesivos.png) | ![Para-brisa, com a coluna no meio](docs/diagnostico-v4/v6-para-brisa.png) |

## Aprendizados aplicados (do MW2005 e deste port)

1. **Limite de índices por peça.** O UG2 fecha o jogo quando uma peça passa de 65.535 índices
   (~21.800 triângulos). O LOD A do Fusion tem ~190 mil triângulos, e o slot FOCUS só desenha
   carroceria, base, porta-malas, roda e adesivos. A pintura foi repartida nessas peças
   (≤ 21.500 triângulos), sem truncar a malha:
   - áreas planas ficam no LOD B; o bico, a frente do teto e o para-choque traseiro usam o LOD A,
     com corte exato (`scripts/clip.py`). Decimar o LOD B por QEM deformava o encontro para-lama/porta;
   - os vidros são uma lâmina nova por janela (`scripts/newglass.py`); o interior foi reduzido para
     caber o LOD A na base. A mancha magenta da v3 e o fechamento na v4 estão na seção anterior.
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
6. **Lente pela peça, não pelo material (v10).** Na v2.7 do MW a lente das lanternas do 2018 passou a usar um
   shader difuso. O build agora reconhece a lente pelo nome `*_GLASS_*`; dentro dela, o grupo com material
   `BRAKELIGHT` é o refletor opaco do 2012 (lição 17 do MW) e continua opaco.
7. **Folha da lanterna pela UV.** O 2012 desenha as carcaças das lanternas na folha do farol e as duas lentes
   na folha da lanterna. Cada lente é uma cópia DXT3 da folha que a UV dela usa; só a da lanterna recebe o
   vermelho forte.
8. **Tração dianteira é 0,0.** No `GlobalB` o valor em 720 é a parte que vai para o eixo traseiro: os FWD do
   jogo gravam 0,0 e os RWD 1,0. O `ports.py` tinha 1,0 para o 2012, o que o deixaria com tração traseira.
9. **Pacote de texturas com identidade própria (v10.1).** O cabeçalho `0x33310001` herdado do MW tinha nome
   vazio e hash `FFFFFFFF`. Com um carro só assim (v9 no Focus) o jogo carregou; com o Focus e o Mustang assim,
   faltaram texturas nos dois (no 2018 só sobraram capô e para-brisa, que usam textura global). Agora cada pacote
   leva o nome, o caminho e o hash que os carros originais usam: `CARTEXTURES`,
   `Global\Pipeline\CarTemplateTextures_<SLOT>.tpk` e o hash desse caminho.
10. **Rodas fixadas nos dois slots.** O registro do Mustang chega com Z 0,17 e raio 0,343. O patch grava X, Y,
   Z, raio e largura aprovados na v9, em vez de herdar os do slot.

## Performance (`scripts/globalb_patch.py`)

- **Motor e câmbio do Toyota Corolla levados a 248 cv** (o 2.0 EcoBoost do Fusion Titanium 2018): todas as
  curvas de torque (estoque, turbo e upgrades) ×2,212; giro e relações do Corolla. Pela curva: 248 cv
  (245 hp) a 6.560 rpm e 288 Nm (Corolla ~111 hp / 130 Nm; Focus original ~125 hp / 182 Nm).
- **Tração**: 2018 integral, divisão de torque 0,5 (valor do Lancer Evo VIII); 2012 dianteira, 0,0. No estoque e nos 3 níveis.
- **Dirigibilidade do Lancer Evo VIII**: pneus, suspensão, direção, freios e tabelas de upgrade;
  massa 1,63 t (Focus 1,15 t, Corolla 0,97 t, Lancer 1,40 t).
- Altura da roda (Z 0,0975), raio 0,3075 e largura 0,195 continuam os do Escort, aprovados no jogo, e agora são gravados nos dois registros.
- **Carro longo**: dimensões 4,73 × 1,85 × 1,46 m e inércia recalculada a partir delas
  (guinada 3,01 contra 2,67 do Evo), além do entre-eixos de 2,74 m (o Focus tinha 2,54 m).

Valores finais em `docs/globalb_2018.json` (`MUSTANGGT`) e `docs/globalb_2012.json` (`FOCUS`).

## Instalação

A v10 foi instalada direto nesta cópia do jogo: `CARS/MUSTANGGT`, `CARS/FOCUS` e o `GlobalB.lzc` gerado por `scripts/globalb_patch.py` (2012 e depois 2018, sobre o arquivo atual). O estado anterior (v9 no Focus, Mustang do mod e GlobalB `689B5935…`) está em `backup/antes-v10-2026-10-06` (fora do git).

Para o 2018 sozinho, feche o jogo e execute `instalar.bat` (na release ele fica ao lado de `CARS`; no repositório, `release/instalar.bat`). O script procura o Underground 2, copia `CARS/MUSTANGGT` e aplica no `GLOBAL/GlobalB.lzc` o mesmo ajuste de `scripts/globalb_patch.py` no registro `MUSTANGGT`: 248 cv, tração integral e chassi do Lancer. Na primeira execução o GlobalB anterior fica em `GLOBAL/GlobalB.lzc.antes-fusion`. Se o arquivo estiver compactado (JDLZ), salve-o descompactado no Nikki e rode de novo.

O backup do estado anterior desta cópia (Escort RS + GlobalB) está em `backup/antes-fusion-2026-09-25` (fora do git).

| Arquivo instalado | SHA-256 |
| --- | --- |
| `CARS/MUSTANGGT/GEOMETRY.BIN` | `44D8DA37D152510BB4DF8209D072351AA35D0E98C025AE71C0659101C1305D05` |
| `CARS/MUSTANGGT/TEXTURES.BIN` | `D57805B128BFF00420C32E7EE06C04E2398834954D9E3F56831E086C72E91170` |
| `CARS/FOCUS/GEOMETRY.BIN` | `A58CF92A698ACAF6859DA379FFA29D9B8787F2499BDF85C0D791E46FDD22C94F` |
| `CARS/FOCUS/TEXTURES.BIN` | `0FA4FE86D41210D3FE39EBAC311111CEDAE770F32C8FF0FDF817A601E5567770` |
| `GLOBAL/GlobalB.lzc` | `0A026C97DBDD588E6E9B263D8EAAFC9DD7B2324C2600B129CE81762809B5A5DB` (`FOCUS` 2012 FWD + `MUSTANGGT` 2018 AWD) |

## Reconstruir

Python 3 + numpy + Pillow. `mw/` é o ZIP da release do Most Wanted extraído (v10: v2.7). O molde de textura é o `CARS/MUSTANGGT/TEXTURES.BIN` do 2018. Cada port roda numa pasta própria, porque `mw_parts.pkl` e `texdump/` são do carro extraído por último.

```
python extract_mw.py 2018     # MUSTANGGT -> mw_parts.pkl e texdump/
python build.py out 2018      # peças MUSTANGGT_*
python extract_mw.py 2012     # COBALTSS, mesma pipeline do 2018
python build.py out 2012      # peças FOCUS_*
python globalb_patch.py GlobalB.lzc GlobalB.2012.lzc 2012
python globalb_patch.py GlobalB.2012.lzc out/GlobalB.lzc 2018
python preview.py out/GEOMETRY.BIN out/TEXTURES.BIN previa.png
```

`BUILD_DRY=1 python build.py out 2012` só imprime o orçamento de cada peça, sem gravar.

| 2018 (`MUSTANGGT`) | 2012 (`FOCUS`) |
| --- | --- |
| ![prévia offline do 2018](docs/previa-fusion-ug2.png) | ![prévia offline do 2012](docs/previa-fusion2012-ug2.png) |

O leitor/escritor de GEOMETRY foi validado reescrevendo o Escort RS: estrutura idêntica chunk a chunk.
O compressor JDLZ foi validado com ida e volta contra o descompressor que lê os blobs do Escort.

## Limites conhecidos

A v9 do 2018 foi aprovada na garagem, no modo exploração e na largada: carroceria completa (teto, portas e capô), faróis, lanternas e rodas dentro dos arcos. A v10 dos dois carros ainda não foi vista no jogo.

- O slot `MUSTANGGT` nunca foi medido no jogo com o Fusion. O mod de Mustang instalado antes não tinha `TRUNK_A`; se a tampa do porta-malas faltar no 2018, é esse slot que não desenha a peça.
- No 2012 o para-choque traseiro e as lanternas externas estão na `TRUNK_A`. Na tela de som eles abrem junto com a tampa.
- O interior perdeu o assoalho (z < 0,30), que não aparece pelas janelas, e ficou mais simples que o da v9: a base do MW cresceu e não sobra orçamento.

- Freios (`KIT00_FRONT/REAR_BRAKE_A`) não entram.
- Na tela de som o jogo anima a `TRUNK_A` com o pivô do slot.
- Logo da tela de seleção (`FrontB.lzc`) e o nome no menu continuam os do Escort/Focus.
- O `VINYLS.BIN` de cada slot continua o do jogo; a pintura usa a UV projetada no molde dele (`FOCUS_DEBUG` ou `MUSTANGGT_DEBUG`, ver `docs/diagnostico-v8/vinil-molde-mustanggt.png`).
- `release/instalar.bat` ainda instala só o 2018.
