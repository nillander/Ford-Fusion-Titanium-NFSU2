# TODO — Fusion Titanium 2018 AWD no NFSU2 (slot FOCUS)

Estado em 26/09/2026 (noite): **v5 instalada, aguardando teste no jogo.** A v5 é a v4 com vidros novos
(gerados do zero, sem frestas). A v4 ataca os itens 1–8 da lista abaixo. Leia também [CONTINUACAO.md](CONTINUACAO.md).

- Instalado agora: GEOMETRY `FC9E24E7…E0F7` (v5), TEXTURES `349F6BEC…26B4` (o da v3, sem mudança),
  GlobalB `27F9944B…CF97` (o original do backup **só com as rodas mudadas**: X +1,431 / −1,311, Y ±0,78).
- Backups (fora do git): v3 em `backup/v3-instalada-2026-09-26/`, GEOMETRY da v4 em `backup/v4-instalada/`.
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

## Se a v4/v5 fechar o jogo

A v4 muda duas coisas ao mesmo tempo em relação à v3 que abriu: a geometria e as rodas no GlobalB.
1. Voltar só o GlobalB do backup (`backup/v3-instalada-2026-09-26/GlobalB.lzc`). Se abrir → o problema
   é a edição das rodas (improvável: são 6 floats).
2. Se ainda fechar → é a geometria. Suspeitas, em ordem: peça `KIT00_TRUNK_A` nova; `BASE_A` com 63.747
   índices (a maior já testada era 61.458, do Senna); 23 mil vértices por peça (Escalade: 17,7 mil).
   Para testar, reduzir o `CAP` em `scripts/build.py` para 20.000 e/ou devolver o porta-malas ao corpo.

## Lista

- [ ] **Testar a v5 no jogo** e conferir os itens 1–8 (fotos novas em `docs/in-game-v4/`).
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
