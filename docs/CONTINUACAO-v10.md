# Estado atual — v10.9 aprovada: friso original branco e lentes opacas (06/10/2026)

v10.8 reprovada visualmente: lanternas/refletores e friso continuam escuros. v10.9 recupera o friso original 2018 de BASE_A/MISC (100 triângulos) em branco e TRUNK, removendo a faixa criada sobre pintura e a peça escura antiga da BASE. Lentes/refletores/milhas opacos usam faces exteriores únicas, sem cópias opostas coincidentes. Textura vermelha clara preservada. Não atribuir a ausência do friso ao 2012: ele existe no MW 2018.

Também restaurada a chave de copyright `181419E5` em LANGUAGES/English.bin. CREDITS/NA_ENGLISH.TXT não controla o texto inicial. Instalado e reaplicado com jogo fechado; backup em `backup/antes-v10.9/`. Validação passou; usuário aprovou o resultado visual: “perfeito”. [Registro e prévias](REPARO-LANTERNAS-2018.md), [TODO](../TODO.md). BIN versionados em CARS e docs/build_log.json consolidados com a v10.9 aprovada, idêntica à instalada. Build local em `local/v10.5/out-lamps-white-single/`.

# Histórico — v10.8 luzes claras e faixa cinza (06/10/2026)

v10.7 exibiu as lanternas, mas escuras, e não mostrou a faixa. Instalado v10.8 com célula vermelha mais clara e faixa cinza opaca sobre as lentes, carroceria e tampa. A faixa da tampa está na peça TRUNK para acompanhar sua abertura. Roda, tampa e banco de peças permanecem iguais. Validação passou. Backup v10.7 em `backup/antes-v10.8/`. GEOMETRY `E1E82EA663BFCB66BED0FFE2C1E092CB7E23A40540F82445089FA4C1703DB6B4`; TEXTURES `D867CD3FAB640A1C39EC1A84936044821015AE0059C249C2779CF296575C4719`. Avaliação visual pendente. [TODO](../TODO.md).

## Estado anterior — v10.7 MISC

v10.6 não teve efeito. v10.7 usou MISC + DULLPLASTIC já visíveis na base para lentes/refletores, com duas células livres vermelha/branca na textura existente. O usuário confirmou que as lanternas apareceram, mas escuras e sem faixa transversal. Backup v10.6 em `backup/antes-v10.7/`, E em `backup/antes-v10.6/`. GEOMETRY `5F3C0750E5BF8FF8493AE9D168109D761DAFBCFC3B2B69F322A5388865347572`, TEXTURES `076DE305750BD6C89E99A974AA5D688A9CCFD8BBEBF7BC2796E8CCB425464146`. [TODO](../TODO.md).

Os estados abaixo são históricos.

# Teste atual — v10.6 lanternas, atlas padrão (06/10/2026)

E abriu, mas usuário mostrou lanternas totalmente ausentes e refletores sem vermelho opaco. Instalado teste que troca o atlas personalizado SOLID_LAMPS por KIT00_BRAKELIGHT padrão, vermelho/branco DXT1 256×256. Mesmas faces e contagens da E, GlobalB intacto. Resultado visual pendente. Backup E em `backup/antes-v10.6/`. GEOMETRY `B8BC0C045CE7FD93E3A35D5576C3F4AE987DA15553CA522B33171AB8E24382E5`; TEXTURES `DD499C805E3EF4E46711F21218C0A5C8B31551A75B6106CF0CF405A402FE01DE`. CARS no repositório ainda E; build já usa nome padrão. [TODO](../TODO.md).

Os estados abaixo são históricos.

# Estado atual — v10.5 funcional (06/10/2026)

Usuário aprovou o teste E: "funcionou normalmente". Versão consolidada no repositório e no padrão da build; GEOMETRY instalado permaneceu o mesmo. Tampa A reduzida na pintura (8.000 triângulos), rodas do 2012 habilitadas junto da tampa. Conjunto 63.444 vértices / 60.777 triângulos. Build padrão reproduz exatamente os arquivos aprovados. GlobalB tem apenas carroceria + ids 10/28 copiados do Focus; copiar todas as peças causou fechamento. Não tratar 65.535 como limite suficiente: teste D abaixo dele também falhou.

Hashes e detalhes no [TODO](../TODO.md). Aparência detalhada das lanternas/milhas, cidade e loja de som ainda não descritas pelo usuário. Instalador genérico ainda não incorpora o patch seletivo do banco. Os testes e backups abaixo são históricos.

# Teste atual — v10.5 E (06/10/2026)

Teste D fechou; mesmo breakpoint e cadeia de chamadas dos anteriores. C restaurado durante a preparação. Instalado E: tampa A com pintura reduzida para 8.000 faces, tampa e rodas habilitadas juntas. Conjunto 63.444 vértices / 60.777 triângulos. Resultado pendente. GEOMETRY `4DD5BB956B26CC04FADFC482570E4FAA2A83F3DCFC9773CC8AEC316E79E9CE9C`. Se falhar, restaurar C e investigar carregamento antes de nova tentativa; 65.535 não se confirmou como limite suficiente. [TODO](../TODO.md).

Os estados abaixo são históricos.

# Teste atual — v10.5 D (06/10/2026)

Usuário respondeu "ok, próximo" ao teste C, interpretado na conversa como funcionando. Instalado teste D: tampa LOD A reduzida na pintura (10.999 triângulos), lanternas preservadas, rodas do 2012 intactas. Conjunto: 65.320 vértices / 63.776 triângulos. Backup do C em `backup/v10.5-teste-C/`. GEOMETRY `E91EC3E9FB4751370D76C7132F6ECCF0E657CD04895917DF2AE12B819644B73A`. Resultado e acabamento pendentes; ver [TODO](../TODO.md).

Os estados abaixo são históricos.

# Teste atual — v10.5 C (06/10/2026)

Tampa e rodas aprovadas separadamente. Instaladas juntas, com **tampa LOD B**, reduzindo o conjunto abaixo de 65.535 vértices/triângulos. Hipótese de limite agregado ainda não comprovada. Base, carroceria, roda e texturas idênticas às da v10.5. Resultado pendente. GEOMETRY `72A1B07232ADB385EBE9A8125FC0A78C24E5D10D0AB384BF0A77CE96DEE4C415`; GlobalB `0D9F51AF2F920E52F5C7AE62BC121F5FDFF1EDFC475F4F6E42A77CAFB3403E2B`. Originais e próximos passos no [TODO](../TODO.md).

Os estados abaixo são históricos.

# Teste atual — v10.5 B (06/10/2026)

Teste A aprovado pelo usuário: a tampa apareceu. Banco aprovado em `backup/v10.5-tampa-aprovada/`. Instalado teste B: **carroceria + roda, tampa desabilitada**, geometria/texturas intactas. GlobalB `A4B190F056DC09876B80C0F22DAA64CE9936DD4E62E0414089B966E8014A37EC`. Resultado pendente; passos no [TODO](../TODO.md).

Os estados abaixo são históricos.

# Teste atual — v10.5 A (06/10/2026)

A v10.5 com tampa e roda habilitadas fechou ao visualizar o Mustang. Instalado teste com **só a tampa** além da carroceria aprovada: roda desabilitada. Geometria e texturas da v10.5 intactas. GlobalB `59E3BC4BA1ACEDAFE7F52B1905B0203FC36953CFF7634824B67B03F1D44FDC8D`. Backup da versão que fechou e dump em `backup/v10.5-fechamento/`. Resultado no jogo pendente; próximos passos no [TODO](../TODO.md).

O estado abaixo registra a v10.5 anterior ao teste A.

# Estado atual — v10.5 (06/10/2026)

A carroceria da v10.4 apareceu nas duas imagens enviadas pelo usuário. Instaladas as quatro correções do 2018; teste no jogo pendente. Ver [TODO v10.5](../TODO.md) e [prévia](in-game-v10.5/previa-bancada.png). Backup anterior: `backup/antes-v10.5/`. O GlobalB atual soma somente os ids 10 (tampa) e 28 (roda) à variante da carroceria que funcionou. A cópia integral das 270 peças, que travou, não foi reaplicada.

- `CARS/MUSTANGGT/GEOMETRY.BIN`: `DF36272E7EA602AB67A9F7439BAB0D48B1CF2D0A5A93F7EC63CD73EBEE9E90BF`
- `CARS/MUSTANGGT/TEXTURES.BIN`: `FBFAEA3378D306B2ABCF0227065B71B21CB3CAB940DEC9E680458D9F6CCE0DD8`
- `GLOBAL/GlobalB.lzc`: `0D9F51AF2F920E52F5C7AE62BC121F5FDFF1EDFC475F4F6E42A77CAFB3403E2B`

O restante deste documento é o registro anterior à v10.5, preservado para diagnóstico.

# Continuação — v10 (reexportação da v2.7 do MW), estado em 06/10/2026 18:05

Leia antes de mexer: [PORTAR-PARA-NFSU2.md](PORTAR-PARA-NFSU2.md) (seções 8 e 9), [TODO.md](../TODO.md) (v10 a v10.4).

## O que está instalado no jogo agora

| Arquivo | SHA-256 | O que é |
| --- | --- | --- |
| `CARS/MUSTANGGT/GEOMETRY.BIN` | `451516A9…D681CA` | Fusion 2018 da v2.7, divisão da v9 (= `CARS/MUSTANGGT` do repositório) |
| `CARS/MUSTANGGT/TEXTURES.BIN` | `D57805B1…E91170` | identidade `CarTemplateTextures_MUSTANGGT.tpk` |
| `CARS/FOCUS/GEOMETRY.BIN` / `TEXTURES.BIN` | ver README | Fusion 2012 v10.3 (grupos unidos) |
| `GLOBAL/GlobalB.lzc` | `E5A03095…DFC3B42` | **variante de teste**: registros `FOCUS` (2012 FWD) e `MUSTANGGT` (2018 AWD) de `globalb_patch.py` + **só** carroceria e carrocerias largas do Mustang no layout do Focus (`globalb_parts.py … FOCUS MUSTANGGT 5,6`) |

Variantes do `GlobalB` desta sessão (fora do git) em `backup/v10-globalb/`: `GlobalB.final.lzc` (v10–v10.3, `0A026C97…`), `GlobalB.parts.lzc` (v10.4, trava), `GlobalB.body.lzc` (teste atual), `GlobalB.orig.lzc` (original do jogo descompactado, para consultar as tabelas de fábrica).

Backups (fora do git): `backup/antes-v10-2026-10-06/` (v9 no Focus, mod de Mustang de 2019, GlobalB `689B5935…`), `backup/antes-v10.4/GLOBAL/GlobalB.lzc` (`0A026C97…`, antes de qualquer mudança no banco de peças).

## Onde paramos

### 2018 no slot do Mustang (prioridade do usuário)

1. Sintoma até a v10.3: só a `BASE_A` aparecia (capô, frente do teto, vidros, grade, placa); sem laterais, porta-malas e rodas. Não era vinil (carro de fábrica).
2. Causa encontrada no banco de peças (`scripts/globalb_carparts.py GlobalB.lzc MUSTANGGT FOCUS` mostra): o mod de Mustang personalizado deixou vazia a entrada do LOD A das tabelas do `MUSTANGGT`; o jogo pedia `MUSTANGGT_KIT00_A` em vez de `MUSTANGGT_KIT00_BODY_A` (idem roda, para-choques, capô; porta-malas sem entrada). O `GlobalB` original (`_backup-ptbr/GlobalB.lzc`, JDLZ) tem as tabelas de fábrica (A–D com `_BODY` etc.).
3. v10.4: todas as 270 peças do Mustang apontando para as tabelas do Focus (`gb/GlobalB.parts.lzc`, `9BBF534A…`). **Resultado: o jogo trava e fecha ao mostrar o Mustang.**
4. Teste em andamento: só ids 5 e 6 (carroceria). Próximos passos conforme o resultado:
   - não trava e aparecem as laterais → somar o porta-malas (`5,6,10`), depois a roda (`28`), depois a base (`0`, pede B e C);
   - trava → a carroceria em si; comparar o registro de atributos da carroceria (2ª lista de atributos: `000004B8` aponta para a peça id 68 do carro) e testar as tabelas de fábrica do Mustang (as do `COROLLA` são as de fábrica e estão intactas no arquivo atual) em vez das do Focus.
   - suspeita principal para o travamento: a roda (o registro do Mustang tem aro padrão 26/18/20 contra 24/16/18 do Focus, offset 220) ou o porta-malas.
5. CarTypeInfo Focus × Mustang: só diferem nome, caminhos, hash do nome (208), aro (220), tração (720…), índice do carro (2112) e dois hashes em 2124/2128.

### 2012 no slot do Focus (depois do Mustang)

Faróis, faróis de milha e lanternas não existem no jogo (vê-se o interior), em todos os modos. O resto do carro aparece. Já descartado:
- textura (bytes do cabeçalho iguais à v9; decodifica certo), cores de vértice (todas 255), UV, normais, posições, DXT1 sem transparência;
- célula preta do farol (corrigida na v10.2, não resolveu);
- grupos repetidos com a mesma textura/material (unidos na v10.3, não resolveu).
Pistas não testadas:
- no layout do Focus, `KIT00_HEADLIGHT` e `KIT00_BRAKELIGHT` não têm LOD A, mas têm entradas 4–6 (`_HEADLIGHT_RIGHT`, `_BRAKELIGHT_TRUNK`): talvez o jogo esconda grupos com material de farol/lanterna dentro de outras peças quando o slot tem peça de luz própria. Na v9 do 2018 as luzes ficavam na mesma `KIT00_BODY_A` e apareciam, então comparar materiais e texturas das luzes da v9 (`HEADLIGHTREFLECTOR` + `FOCUS_KIT00_HEADLIGHT`) com as do 2012 na mesma peça;
- testar o 2012 com as luzes do 2018 (mesmo código, malha que já apareceu) para separar malha de slot;
- testar as luzes do 2012 dentro da `BASE_A`.

## Ferramentas e cuidados desta sessão

- Trabalho fora do repositório: uma pasta por port (`~/w/2018`, `~/w/2012` no shell do computador) com cópia de `scripts/`, `docs/`, `CARS/` e `mw/` (ZIP da release extraído). `BUILD_DRY=1 python3 scripts/build.py out 2012` mostra o orçamento.
- O shell do computador encerra processos em segundo plano no fim de cada chamada: rodar extração e build em primeiro plano (≤ 180 s cada).
- Git a partir do shell: `git-lfs` 3.5.1 baixado para `~/bin`; usar `-c core.autocrlf=true` (o Windows guarda LF e o README fica CRLF na pasta). Apagar `.git/index.lock` precisa da permissão de exclusão da pasta.
- `globalb_patch.py` grava X/Y/Z, raio e largura das rodas; 2012 com tração 0,0. `globalb_parts.py` copia o layout de peças entre slots (5º argumento = ids de peça).
- Lição de método: a v10 mudou muitas variáveis por teste (slot novo, 2012 novo, cabeçalho do TPK, GlobalB). Voltar a "uma variável por teste" (regra 5 do guia).
