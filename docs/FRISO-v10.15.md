# Variante de diagnóstico após o fechamento — v10.15

O usuário confirmou que a v10.13 restaurada abriu normalmente. Isso estabelece uma referência funcional após a falha v10.14 ao visualizar o carro.

O dump `%LOCALAPPDATA%/CrashDumps/SPEED2.EXE.23360.dmp` aponta para INT3 em `0x43BD50`, retorno `0x63A265`, pela rotina de carregamento. Esse retorno também apareceu nas falhas anteriores da combinação tampa + roda, documentadas na lição 10 de PORTAR-PARA-NFSU2. A comparação v10.13/v10.14 mostrou apenas mudança de UVs; não prova que as cores ou coordenadas causaram a interrupção. Falta de margem no carregamento é uma hipótese, não causa confirmada.

Como diagnóstico, a v10.15 mantém os dois acabamentos da v10.14 e reduz apenas a pintura da tampa de 8.000 para 6.000 faces. Lanternas, friso, dimensões, texturas e rodas foram preservados. Comparação dos BIN confirmou que os buffers das superfícies MISC das lanternas/friso são idênticos à v10.14; as peças não relacionadas permaneceram iguais. O sólido TRUNK passa a 7.515 triângulos / 8.590 vértices. O BIN de geometria passa de 7.268.224 para 7.204.352 bytes. Essa redução é um teste; só o jogo pode confirmar estabilidade, e a pintura simplificada também requer avaliação visual.

Reconstrução: executar em `local/v10.5` com `BUILD_TRUNK_PAINT_TARGET=6000` e `python ../../scripts/build.py out-lamps-two-finishes-light 2018`. Após a aprovação do usuário, 6.000 passou a ser o padrão do port; a variável de ambiente não é mais necessária para reproduzir a v1.2.

Validação estrutural passou. GEOMETRY SHA-256 `DB4CDE8C5964DCC2C121A525C7BC46F71B3C4A13B25F2173C08F4C85F8F175BA`; TEXTURES `92B437E1BE6B57CD9FEBDD4425920BBC70F9649D9D04576BBFAF20C2B896C50B`. Instalado com jogo fechado e hashes conferidos. Backup funcional v10.13 em `backup/antes-v10.15/CARS/MUSTANGGT/`. O usuário confirmou: “está funcionando, está quase perfeito”, e autorizou commit, tag e release. Consolidada na release pública v1.2.

## Consolidação pública v1.2

BIN versionados em CARS/MUSTANGGT e docs/build_log.json atualizados com o pacote instalado aprovado. Código configurado para 6.000 faces por padrão. Prévias finais em `in-game-v10.15/`; pacotes dos dois veículos incluem instaladores e manifestos. O 2012 mantém seus BIN da v1.1 e a pendência de validação das luzes.
