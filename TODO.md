# TODO — Fusion Titanium 2018 AWD no NFSU2 (slot FOCUS)

Estado em 27/09/2026: **v9 instalada, aguardando teste no jogo.** A v8 abriu mas sem teto, portas e capô (ver abaixo). A v6 ataca os itens A, B e C do teste da
v5 (adesivos, para-brisa, traseira). A v5 trouxe os vidros novos (gerados do zero, sem frestas). A v4 ataca os itens 1–8 da lista abaixo. Leia também [CONTINUACAO.md](CONTINUACAO.md).

- Instalado agora: GEOMETRY da v9 (SHA em README), TEXTURES `830FD72B…457F` (o da v6),
  GlobalB `27F9944B…CF97` (o original do backup **só com as rodas mudadas**: X +1,431 / −1,311, Y ±0,78).
- Backups (fora do git): v3 em `backup/v3-instalada-2026-09-26/`, GEOMETRY da v4 em `backup/v4-instalada/`,
  GEOMETRY + TEXTURES da v5 em `backup/v5-instalada/`, da v6 em `backup/v6-instalada/`, GEOMETRY da v8 em `backup/v8-instalada/`.
- Diagnóstico: `docs/diagnostico-v4/` (magenta = face vista por trás, que o jogo não desenha → buraco;
  verde = normal do vértice contrária à face → mancha escura).

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

- [ ] **Testar a v9 no jogo** (carro completo; vinis; adesivos; traseira/bico/teto).
- [ ] Para usar mais LOD A seria preciso descobrir como o slot pode desenhar mais peças (ex.: editar a lista de
  peças do FOCUS no GlobalB, que o instalador `.u2car` alterou), ou o jogo aceitar dois sólidos com o mesmo
  nome (o mod Focus RS tem dois `FOCUS_BASE_A`; não confirmado).

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
- [ ] Se os adesivos continuarem sem aparecer: comparar com um mod que comprovadamente mostra adesivos
  (Mustang em `source/`) instalando-o num slot de teste; testar decal com matriz/`0x134017-19` do Corolla.
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

- [ ] **Testar a v6 no jogo** (adesivos em vidros/portas/capô, para-brisa, lanternas, tampa e para-choque).
- [x] Testar a v5 no jogo: abriu. Novos problemas em "Problemas vistos no teste da v5" (A, B, C).
- [ ] **0. Teste B — GlobalB com performance.** Depois que a v4 for aprovada, aplicar
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
- [ ] Commit local ao final de cada etapa (sem push).
