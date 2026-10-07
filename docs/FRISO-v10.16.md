# Gradiente metálico do friso e branco claro das lentes — v10.16

A v1.2 funciona, mas a nova captura mostrou friso e lentes com aparência plana e escura. O usuário pediu o formato atual com o acabamento anterior: gradiente metálico no friso e branco claro nas lentes.

![Formato atual a preservar](in-game-v10.16/antes-v1.2.png)

![Referência de acabamento](in-game-v10.16/referencia-acabamento.png)

As normais uniformizadas em (−1,0,0) retiravam a variação de iluminação do friso e a orientação original das lentes. A v10.16 retoma as normais dessas superfícies e a correção geral de normais da exportação. O friso recebe um gradiente vertical cinza/branco na célula existente de 32×32 do MISC; os UVs acompanham a altura, com o mesmo mapeamento nas partes internas e externas. O branco das lentes continua separado, na célula de branco claro já existente. Mantidos DULLPLASTIC, alfa opaco e a pintura da tampa em 6.000 faces.

![Prévia traseira compilada](in-game-v10.16/previa-rear.png)

![Prévia angular compilada](in-game-v10.16/previa-angle.png)

A comparação com a v1.2 confirmou posições, índices, grupos e materiais idênticos em todos os sólidos. Não foram criadas superfícies nem alteradas as pontas. Os tamanhos dos BIN e dos buffers de texturas permaneceram iguais. Na textura decodificada, somente a célula do friso mudou; vermelho, branco das lentes e demais texturas foram preservados. Os 334 vértices do friso usam o gradiente e os 166 das lentes mantêm sua célula branca. A validação estrutural passou. O efeito é pintado na textura e iluminado pelas normais; não depende de um novo shader cromado.

GEOMETRY SHA-256 `AC6C20C8026AB646A771B093A2115A5C90902CFB776683A716C8304305CEDB5D`; TEXTURES `F9E91763B702B88CAC9F6A7F87843DCC7BF503C1BDB1D1DDD88DC7E84F19D2D0`. Instalado com jogo fechado e hashes conferidos. Backup da v1.2 em `backup/antes-v10.16/CARS/MUSTANGGT/`; candidato em `local/v10.5/out-lamps-metallic-gradient/`. O usuário aprovou o resultado no jogo (“perfeito”) e autorizou a publicação. BIN versionados e docs/build_log.json consolidados com os arquivos testados para a release v1.3.

Aprendizado: acabamento uniforme não exige normais constantes nem friso de cor plana. A consistência deve preservar a textura comum a cada região e permitir o gradiente metálico e a iluminação característica das lentes.

## Publicação v1.3

Reconstrução padrão conferida contra os BIN instalados aprovados; ZIPs com instaladores e manifestos SHA-256. O pacote do 2012 mantém os BIN anteriores e sua pendência de validação das luzes. As versões públicas anteriores permanecem disponíveis.
