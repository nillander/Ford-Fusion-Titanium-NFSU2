# Carroceria do 2012 mais lisa — v12

Pedido do usuário (07/10/2026): a lataria do 2012 aparecia craquelada perto dos faróis, na lateral, nas portas e no para-lama traseiro.

## Causa

O orçamento do 2012 obriga a decimar a pintura LOD B de 21.049 para 15.200 triângulos. A decimação recalculava as normais a partir das faces simplificadas. Na exportação, outras 2.352 normais do BODY eram trocadas pela normal dura das faces. O shader de pintura do UG2 reflete o ambiente pela normal de cada vértice, então essas normais irregulares viram manchas e blocos.

## Correção

`normals_from_A` em `scripts/ports.py` / `smooth.transfer_normals`: cada vértice da pintura (BODY, TRUNK, capô e bico) recebe a média, ponderada pela distância, das normais originais do LOD A em até 3 cm. Entram só as normais que concordam com a face do vértice, o que preserva vincos e o outro lado de painéis finos. Posições, triângulos, UVs, grupos e texturas não mudam; só as normais. O tamanho dos BIN é idêntico, então a memória do carro não muda.

Variantes testadas e descartadas: normais recalculadas da superfície LOD A (mais ruído na frente e na traseira) e relaxamento entre vizinhos (blocos mais planos).

| Antes (v11.1) | Depois (v12) |
| --- | --- |
| ![Antes](carroceria-2012-v12/antes.png) | ![Depois](carroceria-2012-v12/depois.png) |

Prévia com listras de ambiente refletidas pelas normais, para expor ondulações: `python scripts/preview_paint.py GEOMETRY.BIN saida.png`. Ela não reproduz o shader do jogo.

Instalado no slot FOCUS, com backup em `backup/antes-v12-2012/`. GEOMETRY `93F5EEC7A0D6EDBA7AA38A09813DED47ED1FD5C03DA134F83D074B8B615F51F6`; TEXTURES igual à v11.1.
