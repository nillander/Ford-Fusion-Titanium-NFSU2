# Ford Fusion Titanium 2018 AWD — Need for Speed Underground 2

Substitui o **Ford Focus** (slot `FOCUS`). O modelo vem do port de Most Wanted 2005 em `fusion-mw2005` e não altera aqueles arquivos.

## O que entra no jogo

- `CARS/FOCUS/GEOMETRY.BIN` — carroceria do Fusion, com o prefixo das peças trocado de `MUSTANGGT_` para `FOCUS_`.
- `CARS/FOCUS/TEXTURES.BIN` — texturas do mesmo port.
- `CARS/FOCUS/VINYLS.BIN` e `PARTS_ANIMATIONS.bin` — adesivos e animações originais do Focus, para o slot continuar completo.

## Potência e dirigibilidade

No `GLOBAL/GlobalB.lzc`, o cartão `FOCUS` ficou assim:

- Curva de torque, giros, turbo e marchas iguais às do **Toyota Corolla**.
- Tração integral: `TorqueSplit = 0.5` (o mesmo valor do Lancer Evo e do Impreza; o Corolla é 1, tração dianteira).
- Entre-eixos alongado para o comprimento do Fusion. A carroceria vai de -2,36 a 2,37 no eixo X (o Focus original vai de -1,96 a 1,78). As rodas dianteiras ficam em X = 1,611 e as traseiras em X = -1,704. A bitola acompanha a largura maior da carroceria (Y = 1,005).

## Instalação

1. Feche o jogo.
2. Faça backup de `CARS/FOCUS` e de `GLOBAL/GlobalB.lzc`.
3. Copie `CARS/FOCUS` para a pasta do jogo, substituindo os arquivos.
4. Nesta instalação, o `GLOBAL/GlobalB.lzc` do jogo já recebeu a potência do Corolla, a tração integral e o entre-eixos longo. Os números estão na seção acima.
