# TODO — Fusion no NFSU2

A partir da tabela em `scripts/ports.py`, o 2018 vai para o slot `MUSTANG` e o 2012 para o slot `FOCUS`. O diário abaixo é a v9, feita quando o 2018 ainda ocupava o `FOCUS`. Essa medição é o que o port do 2012 reaproveita.

# Diário da v9 — Fusion Titanium 2018 no slot FOCUS

Estado em 27/09/2026: **finalizado e aprovado no jogo.** Capturas em `docs/in-game-final/`. O resultado publicado está no [README.md](README.md).

Pedido: portar o Ford Fusion Titanium 2018 AWD do MW2005 (`C:\Users\nillander\NoDocuments\fusion-mw2005`, V1prime-z10; aqueles arquivos não são alterados) para o slot do Ford Focus, com o Escort RS (`source/Ford-Focus-ESCORT-RS`) como doador de estrutura. Performance: motor do Corolla levado a 248 cv, tração integral e dirigibilidade do Lancer Evo VIII.

A v8 abriu mas sem teto, portas e capô (ver abaixo). A v6 ataca os itens A, B e C do teste da
v5 (adesivos, para-brisa, traseira). A v5 trouxe os vidros novos (gerados do zero, sem frestas). A v4 ataca os itens 1–8 da lista abaixo. As v1–v3 explicam por que o jogo fechava na seleção.

- Instalado: GEOMETRY da v9 e TEXTURES `830FD72B…457F` (SHA no README), GlobalB de performance `689B5935…2462`.
  O GlobalB anterior, só com as rodas (X +1,431 / −1,311, Y ±0,78), é o `27F9944B…CF97` em `backup/v9-antes-performance/`.
- Backups (fora do git): v3 em `backup/v3-instalada-2026-09-26/`, GEOMETRY da v4 em `backup/v4-instalada/`,
  GEOMETRY + TEXTURES da v5 em `backup/v5-instalada/`, da v6 em `backup/v6-instalada/`, GEOMETRY da v8 em `backup/v8-instalada/`.
- Diagnóstico: `docs/diagnostico-v4/` (magenta = face vista por trás, que o jogo não desenha → buraco;
  verde = normal do vértice contrária à face → mancha escura).

## v1–v3 — o jogo fechava na seleção

| Versão | O que muda | Resultado no jogo |
| --- | --- | --- |
| v1 (`28a6a9c`) | peças até 62.886 índices / 24.303 vértices; sólidos fora da ordem de hash; TPK JDLZ; GlobalB com performance | fechou ao selecionar o carro |
| v2 (`f3ff5b4`) | peças ≤ 46.500 índices / 19 mil vértices; sólidos em ordem de hash; resto igual à v1 | fechou ao selecionar o carro |
| v3 — teste A | GEOMETRY da v2 + TPK sem compressão (RAWW, layout do mwtc) + GlobalB original | abriu, com rodas fora do lugar, vidros furados, capô manchado e lanternas sem lente |

A v2 também fechou, então o tamanho das peças e a ordem dos sólidos não eram o único problema. A v1 e a v2 compartilhavam o compressor JDLZ próprio: cópias de até 4.098 bytes (o nfsu360 no Escort chega a 710) e o blob sem o byte extra que o nfsu360 deixa. A v3 grava RAWW, como o `mwtc`, e foi essa troca que fez o carro abrir. O GlobalB com performance ficou para o teste B, feito na build final.

SHA do teste A: GEOMETRY `54AB592E…A5E1`, TEXTURES `349F6BEC…26B4`, GlobalB `10A8EAE6…BBB9` (backup, sem alteração). O GlobalB de performance da v3, sem mexer no aro, está em `variantes/performance/GlobalB.lzc` (`F45D3B2D…8926`, fora do git).

Híbridos preparados para bissectar a geometria, e que não foram necessários: `variantes/hibridos/`, gerados por `scripts/hybrids.py`, para usar com `TEXTURES_uniao.BIN` e o GlobalB original. `H0_escort_regravado` (Escort reescrito por `ug2write.py`), `H1_base`, `H2_body`, `H3_roda`. O port antigo do Cursor está em `backup/port-antigo-cursor/` (GEOMETRY de 31 MB, 159 peças, flags 0x4080, TPK do MW); não se sabe se ele chegou a exibir o carro.

A montagem da v2 usava LOD C decimado (carroceria e base em torno de 15.500 triângulos, roda LOD B com 8.614). Decimar o LOD A/B por QEM deformava a junção para-lama/porta; a v4 em diante deixa de fazer isso.

## O que a v4 mudou (causas encontradas)

| Item | Causa | Correção na v4 |
| --- | --- | --- |
| 1, 2 rodas | GlobalB original tinha as rodas do Escort (X +1,26 / −1,28) | só X e Y das 4 rodas no GlobalB (`scripts/globalb_wheels.py`); Z, raio e performance intactos |
| 3 porta dianteira direita | pintura era o LOD C decimado de novo (14.802 → 14.000) | pintura agora é o **LOD B inteiro** (26.062 → 25.477 sem as faces internas duplicadas), sem decimação |
| 4, 8 vidros | o vidro do MW é dupla face (camada de fora + de dentro) e metade das peças fica na `REAR_WINDOW_A`, que não tinha entrado; a decimação 12k → 1,5k juntou as duas camadas e abriu buracos | junta `FRONT_WINDOW_A` + `REAR_WINDOW_A`, **fica só com a camada de fora** (10.715 faces) e decima 10.715 → 3.500 numa superfície só |
| 5 lanternas | a lente usava o material `BRAKELIGHTGLASS`, que nos carros originais é só o brilho de frenagem; e metade das faces da lente está virada para dentro | lente com material `BRAKELIGHT` e **dupla face**; carcaça com `DULLPLASTIC` |
| 6 traseira | LOD C + decimação | LOD B sem decimação; a tampa do porta-malas foi para a peça `KIT00_TRUNK_A` (o Escort também usa essa peça) |
| 7 capô | o capô do MW é dupla face coincidente (em cima e embaixo no mesmo lugar); com a decimação as duas camadas se misturaram (manchas pretas) | **capô LOD B só com a face de cima** (2.728 triângulos), sem decimação, na `BASE_A` |

Peças da v4 (limite adotado: 21.500 triângulos = 64.500 índices por peça):
`KIT00/KITW01–04_BODY_A` 20.232 (pintura LOD B sem porta-malas + faróis) · `KIT00_TRUNK_A` 6.670 (tampa do
porta-malas) · `BASE_A` 21.249 (base C, capô B, vidros, lanternas, interior, motorista) · roda 8.614.
Os kits do MW são a mesma malha no LOD B, então as 5 carrocerias são iguais.

## v5 — vidros novos

Mesmo na v4 ficavam frestas entre o vidro e a moldura (o vidro do MW termina antes da carroceria).
A v5 gera os vidros do zero pelo método dos carros originais do UG2 (uma lâmina simples de face única por
janela, que entra por baixo da moldura), aproveitando do Fusion só o formato:
`scripts/newglass.py` pega a camada externa do vidro do MW, separa as 12 janelas, ajusta uma superfície
lisa (polinômio de grau 6 no plano de cada janela; erro máximo 1,3–3,5 mm), alarga o contorno 30 mm e
dobra essa borda para dentro do carro (0,35 m/m) para ficar escondida sob a moldura, e faz uma malha
nova (Delaunay, pontos a cada 6 cm; 3.174 triângulos no total). O resultado fica em `docs/vidros_v5.npz`
(o `newglass.py` precisa de scipy e contourpy, que não estão no Python do computador; o `build.py` só lê o
`.npz`). Textura continua a `WINDOW` (as texturas por janela dos carros originais não existem como
globais nos arquivos do jogo). Imagens: `docs/diagnostico-v4/v5-vidros-*.png`.
A faixa preta com o triângulo no alto do para-brisa é a cerâmica do Fusion real (peça da base), não defeito.

## v9 — correção da v8

**Teste da v8 (27/09, `docs/in-game-v8/`):** o carro apareceu sem teto, sem portas e sem capô (motor à mostra).
**Causa:** o slot FOCUS, como configurado pelo mod do Escort, só desenha `BODY` (e KITW), `BASE`, `TRUNK`,
`FRONT_WHEEL` e os adesivos. As peças `KIT00_ROOF_A` e `KIT00_DOOR_LEFT/RIGHT_A` são ignoradas.
**Regra:** toda a pintura tem de caber nessas peças (≤ 21.500 triângulos cada).

A v9 volta a esse layout e mantém o que a v8 trouxe de bom:
- pintura LOD B (sem porta-malas; 16.964 → 14.900 nas áreas planas) + **LOD A** no para-choque traseiro
  (x < −1,9), no bico (acima da grade) e na frente do teto (junto ao para-brisa), com cortes exatos;
  tampa do porta-malas LOD A na `TRUNK_A`; capô LOD B (só a face de cima), bico A e frente do teto A na `BASE_A`;
- bico sem o emblema Ford e com o rebaixo preenchido;
- **UV de vinil no molde do Focus** em toda a pintura (`scripts/vinyluv.py`);
- limites reais nos grupos; escapamentos/difusor da base B;
- interior reduzido (≈ 3.700 triângulos) para dar lugar ao LOD A.

Peças: carrocerias 21.228 · `TRUNK_A` 18.021 · `BASE_A` 21.255 · roda 8.614 + adesivos.

- [x] **Testar a v9 no jogo** — aprovado em 27/09 (garagem, cidade e largada): `docs/in-game-final/`.
- [ ] Para usar mais LOD A seria preciso descobrir como o slot pode desenhar mais peças (ex.: editar a lista de
  peças do FOCUS no GlobalB, que o instalador `.u2car` alterou), ou o jogo aceitar dois sólidos com o mesmo
  nome (o mod Focus RS tinha dois `FOCUS_BASE_A`; não confirmado. O arquivo saiu de `source/`).

## v8 — o que mudou (teste da v6: deformações, emblema, vinis)

- **Pintura inteira do LOD A (o mais detalhado), sem nenhuma decimação.** Para caber no limite por peça, ela
  foi dividida nas peças que os carros originais usam e que o jogo desenha com qualquer kit:
  `KIT00_BODY_A` (e KITW01–04) 19.707 · `KIT00_ROOF_A` (teto acima da linha de cintura z > 0,95 + capô
  LOD A) 18.685 · `KIT00_DOOR_LEFT_A` 17.718 · `KIT00_DOOR_RIGHT_A` 13.427 (portas = faixa |x| < 1,1 m) ·
  `KIT00_TRUNK_A` 18.021. Os cortes são exatos (`scripts/clip.py`): as peças se encontram sem degrau.
  Isso resolve de uma vez as ondulações/deformações da traseira, do para-choque, das portas e do teto
  (vinham da malha LOD B/C mais pobre).
- **Emblema Ford do bico removido** (46 triângulos da base) e **rebaixo preenchido**: uma superfície lisa
  ajustada ao redor dele empurra 97 vértices da pintura para fora e recebe normais lisas.
- **Escapamentos e difusor** vêm da base LOD B (a C era grosseira).
- **Vinis.** Causa encontrada: a pintura usava a UV do MW, mas os vinis do UG2 são desenhados sobre o molde
  UV de cada carro. O `VINYLS.BIN` do Focus traz o molde sem compressão (`FOCUS_DEBUG`, salvo em
  `docs/diagnostico-v8/FOCUS_DEBUG-molde.png`). A pintura agora recebe UVs planas nesse molde
  (`scripts/vinyluv.py`): lado esquerdo em cima, teto no meio, lado direito embaixo, frente e traseira
  embaixo à esquerda/direita, escala tirada dos círculos das rodas do molde (u 0,251/0,803 ↔ eixos
  −1,311/+1,431). A orientação foi conferida no Corolla original (mesma convenção); render de conferência:
  `docs/diagnostico-v8/vinil-molde-focus.png` (LEFT/RIGHT/TOP aparecem legíveis nos lugares certos).
- **Adesivos (para-brisa, portas).** Nenhuma diferença de nome foi encontrada (os nomes batem com o que o
  GlobalB monta). Diferença corrigida: os grupos de todas as peças agora gravam os limites reais (os
  originais fazem assim; o nosso gravava ±5000) e o cabeçalho grava o raio da peça. Se ainda não aparecerem,
  ver pendência abaixo.
- Interior 21.300 − fixo (5.1k → 6,2k triângulos), motorista 700.

Peças: 35 sólidos, maior `BASE_A` 21.298 (63.894 índices). Imagens: `docs/diagnostico-v8/`.

### Pendências depois da v8
- [ ] **Testar a v8 no jogo**: vinis na carroceria, adesivos no para-brisa/portas/capô, traseira, bico, teto.
- [ ] Se os adesivos continuarem sem aparecer: comparar com um mod que comprovadamente mostra adesivos,
  instalando-o num slot de teste; testar decal com matriz/`0x134017-19` do Corolla. O Mustang Shelby
  saiu de `source/`: os nomes `DECAL_*` já tinham sido conferidos e a v9 aprovada desenha o carro.
- [ ] Se os vinis saírem deslocados/esticados: ajustar escala vertical `S_V` e os deslocamentos de frente/
  traseira em `scripts/vinyluv.py` pelas fotos.
- [ ] A peça `TRUNK_A` inclui a parte da lanterna central (anima junto com a tampa na loja de som).

## v6 — o que mudou (itens A, B, C)

- **A. Adesivos.** Criadas as peças de posicionamento que os carros originais têm (cada vaga é uma malha com
  UV 0–1, textura global `DUMMY_DECAL1..8` = `910E6654..665B` e material `DECAL` = `02A05578`, nomes
  confirmados no GlobalB): `FOCUS_DECAL_FRONT_WINDOW_WIDE_MEDIUM_A`, `…REAR_WINDOW_WIDE_MEDIUM_A`,
  `…LEFT/RIGHT_DOOR_RECT_MEDIUM_A` (6 vagas), `…LEFT/RIGHT_QUARTER_RECT_MEDIUM_A`, `…HOOD_RECT_MEDIUM_A`
  (4 vagas), `…HOOD_RECT_SMALL_A` (8 vagas) e as cópias `FOCUS_WIDE1..4_DECAL_…` de portas/laterais para as
  carrocerias largas. Vidros, portas e laterais vêm das peças de adesivo do MW (as vagas extras do MW
  `D0161A90`/`445A675D`, números de corrida, ficaram de fora), subdivididas e projetadas no ponto mais
  próximo da pintura/vidro novos, 4–5 mm por fora e com os triângulos virados para fora. O MW não tem
  adesivos de capô: o layout é o do Corolla (`docs/decal_capo_corolla.npz`), com um retângulo por vaga
  deitado sobre o capô do Fusion. Script: `scripts/decals.py`.
- **B. Para-brisa.** Tiradas da base as peças pretas (borda de cerâmica e triângulo do retrovisor) que ficavam
  a menos de 15 mm do para-brisa/vidro traseiro e atravessavam o vidro novo (336 triângulos de `LOGO`, 3 de
  `MISC`). As cunhas escuras que sobram na base do vidro são as palhetas do limpador.
- **C. Traseira.** Tampa do porta-malas agora do **LOD A** (17.450 → 16.365 sem as faces internas; a
  `TRUNK_A` tinha folga). Lanternas do **LOD B**; a parte central, que fica na tampa, foi para a `TRUNK_A`.
  Lente com vermelho vivo (a textura do MW era 98,0,0 porque o MW acende a lente com emissão; agora 238,0,0).
  As faixas pretas dos para-choques eram faces viradas para dentro (o MW desenha as duas faces, o UG2 não):
  as peças `LOGO`/`MISC` baixas da frente e da traseira ficaram dupla face. Normais que apontavam contra a
  própria face (manchas escuras) foram recalculadas em todas as peças (663 na carroceria, 1.079 no
  porta-malas, 2.180 na base).

Peças: carrocerias 20.232 · `TRUNK_A` 18.021 · `BASE_A` 21.145 · roda 8.614 · 32 peças de adesivo.
Imagens: `docs/diagnostico-v4/v6-*.png`.

## Problemas vistos no teste da v5 (26/09/2026, 22:48) — para a próxima sessão

Capturas: `docs/in-game-v5/` (cópia em `Need for Speed Underground 2/_fusion-screenshots/`).

- [x] (v6) **A. Adesivos não aparecem** no para-brisa, no vidro traseiro e nas portas.
  Suspeita: o UG2 desenha os adesivos em peças próprias de posicionamento (`<CARRO>_DECAL_FRONT_WINDOW_…`,
  `_DECAL_REAR_WINDOW_…`, `_DECAL_LEFT/RIGHT_DOOR_RECT_…`, `_DECAL_LEFT/RIGHT_QUARTER_…`,
  `_DECAL_HOOD_RECT_…`), que o Corolla original e o mod do Mustang têm e o nosso GEOMETRY não tem
  (nem o Escort). O MW do Fusion tem essas peças (`MUSTANGGT_KIT00_DECAL_LEFT_DOOR_RECT_MEDIUM_A`,
  `MUSTANGGT_DECAL_FRONT_WINDOW_WIDE_MEDIUM_A` etc., 13–65 triângulos). Plano: listar os nomes completos
  (por hash) das peças DECAL do Corolla/Mustang UG2, portar as do MW com os nomes `FOCUS_…` e conferir
  materiais/texturas que elas usam. Conferir também se os adesivos de lateral dependem da UV da pintura
  (`VINYLS.BIN` do Focus).
- [x] (v6) **B. Falha no para-brisa** (`v5-frente-perspectiva.png`): triângulo escuro no alto e faixa escura
  serrilhada na base do vidro. O triângulo é a peça `LOGO` da base C (x 0,36–0,64, z 1,06–1,20), que fica
  por fora do vidro — tirar da base ou empurrar para dentro do vidro. A faixa de baixo pode ser a borda nova
  do vidro (dobrada 3 cm para dentro) cruzando o painel/limpadores, ou a mesma peça `LOGO`: testar a borda
  com dobra menor só na base do para-brisa e renderizar essa região com a base inteira.
- [x] (v6) **C. Traseira deformada** (`v5-traseira.png`): lanternas escuras/cinza, sem o vermelho da lente, e
  tampa do porta-malas e para-choque com ondulações no reflexo.
  - Lanternas: a lente com `BRAKELIGHT` + dupla face ainda não aparece vermelha. Testar a lente opaca
    (DXT1 vermelha, sem alfa), conferir a ordem de desenho e comparar com a lanterna do Corolla/Golf
    originais (usam texturas globais `D947F346`/`02B52399` e o material `12C9453C`).
  - Tampa/para-choque: o reflexo do UG2 (pintura com mapa de ambiente) mostra as facetas e as normais do
    LOD B. Verificar normais da `KIT00_TRUNK_A` e da traseira da carroceria (recalcular normais suaves
    por posição, respeitando só as quinas vivas) e se a divisão corpo/porta-malas criou normais diferentes
    na emenda.

## Se a v4/v5 fechar o jogo

A v4 muda duas coisas ao mesmo tempo em relação à v3 que abriu: a geometria e as rodas no GlobalB.
1. Voltar só o GlobalB do backup (`backup/v3-instalada-2026-09-26/GlobalB.lzc`). Se abrir → o problema
   é a edição das rodas (improvável: são 6 floats).
2. Se ainda fechar → é a geometria. Suspeitas, em ordem: peça `KIT00_TRUNK_A` nova; `BASE_A` com 63.747
   índices (a maior já testada era 61.458, do Senna); 23 mil vértices por peça (Escalade: 17,7 mil).
   Para testar, reduzir o `CAP` em `scripts/build.py` para 20.000 e/ou devolver o porta-malas ao corpo.

## Lista

- [x] **Testar a v6 no jogo** — superado pela v8/v9; a v9 aprovada está em `docs/in-game-final/`.
- [x] Testar a v5 no jogo: abriu. Novos problemas em "Problemas vistos no teste da v5" (A, B, C).
- [x] **0. Teste B — GlobalB com performance: faz parte da build final** (`689B5935…2462`, gerado sobre o GlobalB
  com as rodas; o anterior em `backup/v9-antes-performance/`). Motor do Corolla com todas as curvas de torque ×2,212
  (248 cv, 288 Nm), AWD 0,5, chassi do Lancer, massa 1,63 t; Z/raio/largura das rodas mantidos os do Escort. Antes disso o menu
  mostrava a potência do Focus porque o patch nunca tinha sido instalado. Plano original: depois que a v4 for aprovada, aplicar
  `scripts/globalb_patch.py` sobre o GlobalB **atual** (já com as rodas) e testar. Se fechar, aplicar o patch
  em partes (chassi do Lancer → motor/câmbio do Corolla → tração 0,5) até achar o bloco.
  Atenção: o patch grava Z = 0,13 e raio 0,3225; na v3/v4 o Z 0,098 e raio 0,308 do Escort ficaram bons
  visualmente — conferir se vale manter os do Escort.
- [x] 1. Roda traseira muito para a frente → X −1,311 (v4).
- [x] 2. Roda dianteira muito para trás → X +1,431 (v4).
- [x] 3. Porta dianteira direita diferente → pintura LOD B sem decimação (v4).
- [x] 4. Buraco no vidro traseiro → `REAR_WINDOW_A` incluída (v4); vidros refeitos sem frestas (v5).
- [x] 5. Lanternas sem lente → material `BRAKELIGHT` + dupla face (v4).
- [x] 6. Traseira deformada → LOD B + `TRUNK_A` (v4).
- [x] 7. Capô com deformações e manchas pretas → capô B, só a face de cima (v4).
- [x] 8. Para-brisa incompleto → idem item 4 (v4).
- [ ] Porta-malas: na tela de som o jogo anima a `TRUNK_A` com o pivô do Focus; ver se fica estranho.

## Depois da lista

- [ ] Logo da tela de seleção (`FrontB.lzc`) e nome no menu ainda são do Escort/Focus.
- [ ] Freios (`KIT00_FRONT/REAR_BRAKE_A`) não incluídos.
- [ ] `VINYLS.BIN` do slot é o do Focus (adesivos podem sair tortos).
- [x] Release `v1.0.0` publicada na `main`.

## Referência — geometria medida no MW

- Arcos: dianteira X = +1,431, traseira X = −1,311 (entre-eixos 2,74 m); para-lama em |y| = 0,91.
- No jogo ficaram Y = ±0,78 e, de altura, o Z, o raio e a largura do Escort (Z ≈ 0,098, raio ≈ 0,308). A primeira gravação usava Z = 0,13, raio 0,3225 e largura 0,235; `scripts/globalb_patch.py` não sobrescreve esses três valores do GlobalB de entrada.
- Marcadores (esquerda/direita trocados em relação ao MW; +Y é o lado esquerdo): faróis (2,15; ±0,577; 0,515), lanternas (−2,22; ±0,653; 0,688), escapamentos (−2,32; ±0,635; 0,135), brake light central, aerofólio (−2,15; 0; 0,868), entrada de ar do teto (0,3; 0; 1,207).

## Referência — formatos

### GEOMETRY.BIN (layout nfsu360)

- Raiz `0x80134000` → chunk vazio → `0x80134001` { `0x134002` (144 bytes: 8 zeros, `0x1D`, nº de peças, "NFS:U2 Geometry Compiler by nfsu360" em 0x38, "DEFAULT" em 0x20, `0x80`), `0x134003` (hash,0), `0x134004` (hash, offset absoluto, tamanho, tamanho, 0, 0), `0x80134008` vazio }.
- Antes de cada sólido um chunk `0x0` de preenchimento para alinhar em 0x80 (sempre, mesmo alinhado), e um no fim do arquivo.
- Sólido `0x80134010`: `0x134011` cabeçalho (12 zeros, versão 0x16, flags 0x40, hash, NumPolys u16, NumVerts u16 = 0, bytes [0, nTex, nLuz, 0], bounds, matriz identidade, 8 zeros, `0xEE580` ×2, 0, 1.0f, NumPolys como float, 0, 0, nome em 28 bytes fixos), `0x134012` texturas (hash,0), `0x134013` materiais de luz (hash,0), `0x13401A` marcadores (80 bytes: hash, 3 zeros, matriz 4×4), `0x80134100` { `0x134900` (68 bytes: 8 zeros, 0x10, 0x4180, nGrupos, 4 zeros, nTris, 3 zeros, nVerts, 3 zeros), `0x134B01` vértices alinhados em 0x80 (36 bytes: pos, normal, cor u32, uv), `0x134B02` grupos de 60 bytes (nº de índices, idx textura, idx material, offset em índices, flags 0x4180), `0x134B03` índices u16 globais do sólido }.
- Os grupos dos carros originais gravam os limites reais. O escritor das primeiras versões gravava ±5000; a partir da v8 os grupos e o raio do cabeçalho são os da peça.
- `scripts/ug2write.py` reescreve o Escort com a mesma estrutura chunk a chunk (só bounds e bytes de preenchimento diferem).
- O slot FOCUS, como o Escort deixou, desenha `BODY` (e KITW), `BASE`, `TRUNK`, `FRONT_WHEEL` e os adesivos. `ROOF` e `DOOR_*` são ignorados.
- Hash = `h = 0xFFFFFFFF; h = h*33 + c` (`scripts/hashes.py`).

### TEXTURES.BIN

- Raiz `0xB3300000` → `0x0` (48) → `0xB3310000` { `0x33310001` (versão 5, caminho "NFS:U2/MW Texture Compiler by nfsu360"), `0x33310002` hashes, `0x33310003` (hash, offset absoluto, tamanho comprimido, tamanho, 0x100, 0) } → `0x0` até 0x80 → blobs em sequência.
- Blob descomprimido = dados + (cauda) + info de 124 bytes + 32 bytes DDS. `ImagePlacement` é cumulativo na ordem de hash. Byte 74: 0x22 = DXT1, 0x24 = DXT3. DXT1 opaca usa classe `1B81E7B0`; DXT3 `001A93CF` com flags de alfa.
- O Escort usa blobs JDLZ. O Fusion instalado grava RAWW (o JDLZ próprio fechava o jogo; ver v1–v3). `scripts/jdlz.py` comprime e `scripts/tpk2.py` descomprime, conferido com os blobs do Escort. Retail usa HUFF (não implementado).
- Pintura: textura global `3C84D757` + material `CARSKIN`. Vidro: textura `WINDOW` + material `WINDSHIELD`.
- Materiais de luz no GlobalB: DULLPLASTIC, INTERIOR, LICENSEPLATE, HEADLIGHTGLASS, HEADLIGHTREFLECTOR, BRAKELIGHT, BRAKELIGHTGLASS, DRIVER, RUBBER, USER_RIMS, CHROME, METPAINTBLACK.

### GlobalB.lzc — CarTypeInfo (chunk `0x34600`, 2.192 bytes por carro)

- O `GlobalB.lzc` desta cópia está descomprimido (salvo pelo Nikki); o original em `_backup-ptbr` é JDLZ. O instalador recusa o arquivo compactado.
- Offsets no registro: 220 bytes de aro (externo, mín, máx); 288 + 48·i = roda i (x, y, z, 0, raio, largura, índice, 2 valores); ordem FL(+y), FR(−y), RR(−y), RL(+y); +y é o lado esquerdo; 544 massa (t), 548–556 comprimento/largura/altura, 560/580/600 inércias (m/12·(a²+b²)); 704–880 câmbio/motor/turbo de estoque (720 = divisão de torque para trás: FWD 0, RWD 1, AWD 0,5; 736 ré, 744+ marchas, 768 marcha lenta, 772 corte, 776 rpm máx, 784–816 curva de torque); 992–1616 tabelas de upgrade de motor/câmbio (divisão de torque também em 1136/1200/1264); 480–704, 880–992, 1616–2032 pneus/suspensão/direção/freios (e upgrades).
- `scripts/globalb_patch.py` (e o `release/instalar.bat`, que grava os mesmos bytes) aplica motor/câmbio do COROLLA com torque ×2,212 (248 cv), chassi do LANCEREVO8, divisão 0,5, X/Y das rodas do Fusion, dimensões 4,73 × 1,85 × 1,46, massa 1,63 t e inércia recalculada. Z, raio e largura da roda ficam os do arquivo de entrada.

## Referência — reconstruir

Os comandos estão no [README.md](README.md). Entradas que o README não nomeia: `mw/` é o ZIP `fusion-mw2005/release/Fusion2018_AWD_MW2005.zip` extraído; `escort/` é o `FOCUS.7z` extraído com `scripts/sevenz.py` (o header é LZMA puro, sem 7-Zip). `python build.py` gera a geometria atual (v9), não o layout da v2/v4. O `globalb_patch.py` roda sempre sobre o GlobalB atual do jogo. Decimador, DXT, JDLZ e o extrator 7z são próprios, em Python e numpy, porque o ambiente não tinha pip.
