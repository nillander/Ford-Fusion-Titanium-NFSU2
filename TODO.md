# TODO — Fusion no NFSU2

A partir da tabela em `scripts/ports.py`, o 2018 substitui o Mustang GT (`MUSTANGGT`, o mesmo nome nos dois jogos) e o 2012 substitui o Focus (`COBALTSS` → `FOCUS`). Os arquivos atuais da release v1.3 estão em `CARS/MUSTANGGT` e `CARS/FOCUS`. O diário abaixo registra a medição feita no slot Focus; essa lista de peças é o que o port do 2012 reaproveita.

# 2012 — manchas nas lanternas (v12.3, 06/10/2026)

O usuário relatou que, mesmo na v1.5, as lanternas do 2012 tinham manchas escuras no vermelho e no branco. A lente DXT3 translúcida (alfa de 221 a 255) deixava a carcaça aparecer por baixo. Na carcaça, cerca de 300 normais eram trocadas na exportação pela média das faces.

- [x] Lente opaca em MISC/DULLPLASTIC, com cor tirada do texel do MW em cada face: 1.161 faces vermelhas e 310 brancas. As normais foram refeitas a partir das faces externas. A textura `FOCUS_CENTRE_BRAKELIGHT` saiu do pacote.
- [x] Carcaça com faces voltadas para fora e normais refeitas. Normais corrigidas na exportação no TRUNK: de 309 para 11.
- [x] Prévia v12.3 com fundo amarelo, enviada pelo usuário: havia frestas entre o vermelho e o branco, entre o vermelho e a carroceria e uma estrela no branco.
- [x] v12.4: duas folhas atrás de cada lanterna, seguindo o contorno da lente: branca atrás do centro (3 mm) e vermelha atrás da lanterna inteira (8 mm). As frestas ficam preenchidas, e nada aparece fora das lanternas. Tentativas descartadas: folha branca ampliada (cobria a borda vermelha) e reclassificar faces vermelhas dentro do centro (gerava dentes brancos). Fica um pequeno filete vermelho na base do branco, que vem da geometria da carcaça. TRUNK: 20.241 triângulos.
- [ ] Conferir no jogo. Backup em `backup/antes-v12.4/`.

# v1.5 — carrocerias lisas nos dois carros (06/10/2026)

- [x] Pacote v1.5 preparado para publish-release.

# 2012 — carroceria lisa (v12, 07/10/2026)

O usuário relatou craquelado perto dos faróis, na lateral, nas portas e no para-lama traseiro. A pintura passou a receber as normais originais do LOD A, sem mexer na geometria. [Registro](docs/CARROCERIA-2012-v12.md).

- [x] Transferir as normais do LOD A para BODY, TRUNK, capô e bico; instalar com backup.
- [x] Conferir no jogo o acabamento da lataria do 2012. Aprovado: "superfície bem lisa".
- [x] Release v1.4: push e tag feitos pelo usuário. A sessão não pode criar nem apagar releases (HTTP 403); comandos `gh` entregues ao usuário.
- [x] v12.1: frente e traseira do 2012 suavizadas, faces da pintura orientadas pelas normais e mesma técnica aplicada ao 2018 (lateral, portas e para-lama traseiro). Instalado nos dois slots.
- [x] v12.1 no jogo: lateral lisa aprovada. Restavam pequenos craquelados nos faróis (2012 e motorista do 2018), traseira e para-lama traseiro do 2012, manchas na lanterna do 2012 e refletores errados no 2018.
- [x] v12.2: traseira do 2012 em LOD A (rebaixo da placa fechado com LOD B), pintura plana decimada do LOD A, lente da lanterna com uma camada, frentes suavizadas nos dois carros, refletores do 2018 com uma camada. [Registro](docs/CARROCERIA-v12.2.md).
- [x] Conferir no jogo a v12.2 nos dois carros e a estabilidade do 2018. Aprovado pelo usuário.

# v1.4 — luzes do 2012 e farol de milha do 2018 (07/10/2026)

# 2012 — luzes ausentes e refletores escuros (v11, 06/10/2026)

Relato do usuário: o 2012 está sem lanternas, faróis e faróis de milha, e os refletores aparecem vermelhos, porém escuros. No 2018, os itens 1–3 (tampa, rodas e lanternas) estão resolvidos.

Causa das luzes ausentes: o `CarRenderInfo` do UG2 só vincula as texturas do carro cujos nomes ele mesmo monta. Entre as strings do SPEED2.EXE estão `%s_MISC`, `%s_SIDELIGHT`, `%s_DOOR_HANDLE`, `%s_CENTRE_BRAKELIGHT` e `<TEXTURE_NAME da lâmpada>_GLASS_OFF`. As texturas `FOCUS_KIT00_HEADLIGHT`, `FOCUS_HEADLIGHT_LENS`, `FOCUS_HEADLIGHT_GLASS` e `FOCUS_BRAKELIGHT_GLASS` nunca eram vinculadas, então seus grupos não eram desenhados. O mesmo explica as tentativas invisíveis do 2018 e por que só MISC funcionou. O Focus original usa exatamente `FOCUS_KIT00_HEADLIGHT_GLASS_OFF` e `FOCUS_SIDELIGHT`. [Registro](docs/LUZES-2012-v11.md).

- [x] Renomear as folhas de lâmpada para nomes vinculados (`tex_alias` em `ports.py`), sem mudar pixels nem geometria.
- [x] Refletores: manter somente a camada voltada para fora, com uma normal plana por refletor (lição v10.9 do 2018).
- [x] Conferir no jogo: faróis, faróis de milha, lanternas e refletores do 2012. O usuário aprovou a v11 ("parece bem").
- [x] Regressão da v11: com o 2012 v11 instalado, visualizar o 2018 fechava o jogo. Ao restaurar o 2012 anterior, o 2018 voltou a abrir (teste A/B do usuário). Hipótese: texturas vinculadas ficam residentes e a memória dos carros já estava no limite, como na v10.14.
- [x] v11.1 instalada: lentes em 128 px, BADGING em 256 px, `HEADLIGHT_GLASS` (41 triângulos) de volta a não vinculada e a folha sem uso removida. Texturas vinculadas somam 581.632 B, contra 614.400 B no candidato que funcionava e 843.776 B na v11. Conferir no jogo o 2018 e a aparência do 2012. Usuário: "perfeito".
- [x] 2018, item 4: o farol de milha aparecia como uma folha plana. A folha branca `backing()` cobria a carcaça. Na v11.2 (`fog_glass`), o farol de milha é desenhado como o farol principal: carcaça com a folha da lâmpada e HEADLIGHTREFLECTOR, lente real com HEADLIGHTGLASS, em LOD B. Ficam 570 triângulos, contra 808 na v1.3; BASE passa de 21.270 para 21.222. Nenhuma textura nova; a folha sem uso `BRAKELIGHT_GLASS` saiu do TPK. Só a BASE mudou. [Prévias](docs/fog-2018-v11.2/).
- [x] v11.2 no jogo: farol de milha escuro, quase invisível. Na v11.3 foi aplicada a mesma estratégia do 2012: `tex_alias` (`MUSTANGGT_SIDELIGHT`, `MUSTANGGT_KIT00_HEADLIGHT_GLASS_OFF`), lente em 128 px e emblemas em 256 px. Texturas: 630.784 B, contra 843.776 B na v1.3. Só a referência de textura mudou; geometria igual à v11.2.
- [x] Release v1.4 publicada com os dois carros; releases e tags antigas removidas a pedido do usuário.
- [x] Conferir no jogo o farol de milha do 2018 v11.3. Aprovado com a v12.2.
- [ ] `FOCUS_DRIVER` também está fora da lista de nomes; o piloto provavelmente não é desenhado. Avaliar depois.

# 2012 — refletores inferiores opacos (06/10/2026)

Aplicada a correção aprendida no 2018: dois refletores com MISC/DULLPLASTIC, vermelho claro opaco e faces exteriores. Ambos vêm no grupo BRAKELIGHT de RIGHT_BRAKELIGHT_GLASS_D; os 20 triângulos e o formato foram preservados. Demais sólidos/texturas permaneceram idênticos. Instalado no Focus com backup; limites, índices, referências e hashes conferidos. [Registro](docs/REFLETORES-2012.md).

- [ ] Conferir os dois refletores e a estabilidade do 2012 no jogo.

# v1.3 — acabamento v10.16 aprovado (06/10/2026)

Usuário aprovou: “perfeito”, autorizando atualização do README, commit, push, tag e release. Consolidados BIN testados, log e prévias do friso metálico em gradiente e das lentes brancas claras. Mantido o formato v1.2 e seu orçamento. Arquivos do 2012 preservados. [Registro](docs/FRISO-v10.16.md).

- [x] Aprovar acabamento no jogo.
- [x] Consolidar os arquivos instalados, documentação e prévias.

# v10.16 — gradiente metálico e branco de lente (06/10/2026)

Usuário pediu o acabamento anterior com o formato da v1.2: friso com gradiente metálico e lente branca clara, sem a superfície plana uniforme entre eles. Retomadas normais de origem e correção geral de exportação; gradiente vertical na célula MISC do friso, com UVs por altura. Célula branca das lentes preservada. Sem mudança de posições, triângulos, materiais ou orçamento. Validação passou; instalado para teste. [Registro e prévias](docs/FRISO-v10.16.md).

- [x] Conferir acabamento e estabilidade no jogo.

# v1.2 — v10.15 aprovada e consolidada (06/10/2026)

Usuário confirmou funcionamento e resultado “quase perfeito”, autorizando commit, tag e release. Consolidados BIN instalados, log, padrão de pintura da tampa em 6.000 faces e novas prévias. Friso com acabamento uniforme próprio; branco inferior das lentes uniforme e distinto. Pacote 2012 preservado. [Registro](docs/FRISO-v10.15.md).

- [x] Confirmar estabilidade e aparência no jogo.
- [x] Consolidar código e BIN da versão aprovada.

# v10.15 — variante de diagnóstico para carregamento (06/10/2026)

Usuário confirmou que v10.13 restaurada abriu normalmente. Dump v10.14 mostra o mesmo retorno 0x63A265 da falha anterior tampa + roda; causa não confirmada. Preparada e instalada, com jogo fechado, variante de pintura da tampa em 6.000 faces. Lanternas/friso e seus dois acabamentos v10.14 permanecem idênticos; validação passou. Backup funcional em `backup/antes-v10.15/`. [Registro](docs/FRISO-v10.15.md).

- [x] Confirmar estabilidade e aparência da tampa no jogo.

# Regressão v10.14 — restaurada v10.13 (06/10/2026)

Usuário informou fechamento ao visualizar o Fusion 2018. Evento Windows às 21:03:09: SPEED2.EXE, exceção 0x80000003, deslocamento 0x0003BD50. O endereço contém INT3; sem pilha/dump, não identifica a condição interna que falhou. MainLog.txt está antigo (25/09), sem registro desta falha. Comparação v10.13/v10.14 encontrou apenas UVs alterados em 166 vértices; posições, índices, normais, cores, grupos, materiais e TEXTURES.BIN iguais. Não atribuir causa ao branco da lente sem evidência.

Restaurados os arquivos v10.13 diretamente do backup, com hashes verificados e validação estrutural aprovada. Arquivos que falharam preservados em `backup/falha-v10.14/CARS/MUSTANGGT/`. Código v10.14 permanece experimental e não deve ser publicado nem instalado novamente sem diagnóstico. A distinção de acabamentos está pendente; aguarda teste do usuário com a versão restaurada.

# v10.14 — dois acabamentos uniformes separados (06/10/2026)

Usuário esclareceu: uniformidade dentro de cada área, não a mesma cor para as duas. Mantida a geometria v10.13. Friso completo usa a célula branca opaca RGB 255/255/255; fundo branco das quatro lentes e inserções inferiores usam a célula branca de lente RGB 238/240/242. Cada acabamento mantém UVs e normais uniformes. O remapeamento de UV agora preserva as células explícitas do atlas, em vez de transformar qualquer U > 0,75 em branco do friso. [Registro](docs/FRISO-v10.14.md).

- [ ] Conferir no jogo a distinção entre friso e branco das lentes.

# v10.13 — contorno mais curto e branco uniforme (06/10/2026)

v10.12 ainda ultrapassava a área frontal da lente externa. Referência nova marca o friso em rosa e o branco inferior em amarelo: são a mesma cor, não as cores da marcação. Faixa externa limitada a |Y| ≤ 0,775 e X ≤ −1,970, antes do deslocamento de 3 mm para trás; recorte vertical Z 0,702–0,728. Friso original da tampa preservado. Todas as superfícies brancas traseiras usam célula RGB 255/255/255, alfa 255, MISC/DULLPLASTIC e normal (−1,0,0).

A correção genérica de normais do exportador alterava algumas dessas normais intencionais; agora preserva apenas as superfícies brancas traseiras identificadas pela célula UV e material. [Registro e prévias](docs/FRISO-v10.13.md).

- [ ] Confirmar no jogo o limite lateral do friso e a uniformidade do branco.

# v10.12 — reversão dos excessos do friso (06/10/2026)

O teste v10.11 mostrou pontas e bordas inferiores além do contorno esperado. Removida a superfície ampliada `front_sheet` e restaurados os recortes v10.10 sobre as lentes existentes. Mantida a textura branca opaca; clareza no jogo depende também do material, das normais e da iluminação. Não ampliar a geometria para tentar compensar escurecimento. [Referências e registro](docs/FRISO-v10.12.md).

- [ ] Usuário conferir o tamanho restaurado no jogo.

# v10.11 — friso mais visível e branco inferior (06/10/2026)

Usuário informou que v10.10 não mudou o suficiente. Substituídas as faixas anteriores por superfícies regradas à frente da profundidade amostrada das lentes. Faixa externa ampliada de 19 para 34 mm (Z 0,697–0,731), em BASE. Painéis inferiores Z 0,662–0,704, em TRUNK: agora a amostragem inclui o friso original, para não ficarem escondidos atrás de sua borda. Cada coluna mantém profundidade constante no pequeno trecho vertical para evitar um lábio escuro voltado para baixo.

Instalado para teste; validação passou. Conjunto 63.066 vértices / 60.003 triângulos. GEOMETRY `DF7DC386D9A1B766A02AD8996C9EE2D61B6CE8B07F2D385EA633EAC9053E2A02`; TEXTURES inalterado `92B437E1BE6B57CD9FEBDD4425920BBC70F9649D9D04576BBFAF20C2B896C50B`. Backup `backup/antes-v10.11/`; candidato `local/v10.5/out-lamps-visible-trim/`. [Detalhes e prévia](docs/FRISO-v10.11.md). Release existente preservada; teste visual reprovado pelos excessos e revertido na v10.12.

- [ ] Usuário conferir faixa externa e branco inferior mais visíveis.

# v10.10 — friso externo e branco abaixo do friso (06/10/2026)

Usuário enviou quatro referências: estado v10.9, traseira real, friso estendido esperado e área inferior branca na lanterna da tampa. Friso original da v10.9 termina na emenda Y ±0,585; adicionadas continuações brancas sobre as lentes externas (na BASE, não na tampa), seguindo tanto a superfície curva vermelha como o fundo branco para não ficarem escondidas. Faixa Z 0,710–0,729. Pequeno painel branco plano Z 0,663–0,688 abaixo do friso nas duas lentes internas, em TRUNK, sem recolorir a borda vermelha inteira. Faces exteriores únicas; mesmo atlas da v10.9.

Instalado para avaliação visual. Validação passou: limites/índices, texturas, opacidade, roda do Focus e chamadas de peças. Backup v10.9 em `backup/antes-v10.10/`; candidato em `local/v10.5/out-lamps-full-trim/`. Conjunto 63.125 vértices / 59.970 triângulos. GEOMETRY `A9E01CD5F50556FDA8B0601119C8166A631A2127314BDCF82D0987F25E0B7B28`; TEXTURES permanece `92B437E1BE6B57CD9FEBDD4425920BBC70F9649D9D04576BBFAF20C2B896C50B`. Referências e prévias em `docs/in-game-v10.10/`. BIN versionados e log atualizados para a release pública v1.1; ajuste visual ainda pendente.

Publicação v1.1 autorizada sem aguardar a finalização do friso. Próximos ajustes seguem v1.2, v1.3 etc., com uma release compartilhada pelos dois veículos.

- [ ] Usuário conferir extensão do friso nas duas partes externas e branco inferior nas duas partes internas.

# v10.9 — friso original branco, lentes sem faces opostas e copyright (06/10/2026)

Usuário reprovou a aparência v10.8: lanternas/refletores e friso continuaram escuros. Confirmado que o friso existe na fonte 2018 do MW, em BASE/MISC; a remoção no 2012 não explica o 2018. A faixa criada sobre a pintura foi removida; recuperado o friso LOD A original (100 triângulos), em branco opaco, anexado a TRUNK. Removidas as cópias opacas coincidentes com normais opostas nas lentes/refletores/milhas. O usuário aprovou a v10.9: “perfeito”. BIN e log consolidados no repositório.

README atualizado com os aprendizados, capturas enviadas e novas prévias compiladas sem inverter normais para a câmera. Detalhes em [REPARO-LANTERNAS-2018.md](docs/REPARO-LANTERNAS-2018.md). Mensagem inicial restaurada somente na chave `181419E5` de `LANGUAGES/English.bin`: © 2004 Electronic Arts Inc. Todos os direitos reservados. A troca anterior de CREDITS não atingia essa mensagem.

Instalado v10.9 e reaplicado após o usuário fechar o jogo. Backup v10.8 e idioma anterior em `backup/antes-v10.9/`. Validação passou; conjunto 62.920 vértices / 59.868 triângulos. GEOMETRY `C1BB98C69F47D35DD57A23FF5A84271B8730905A1EE96EC99518FFE965CC6B5C`; TEXTURES `92B437E1BE6B57CD9FEBDD4425920BBC70F9649D9D04576BBFAF20C2B896C50B`; English `3F54514EE3527B87D24855E3B9DEDBC3060B214C5158CC4AAC05F3F5C8142CAA`.

- [x] Usuário aprovou copyright, lanternas/refletores e friso: “perfeito”.
- [ ] Conferir friso acompanhando abertura da tampa.

# v10.8 — lanternas claras e faixa traseira cinza (06/10/2026)

O teste v10.7 fez as lanternas aparecerem, mas ficaram escuras e o friso não era visível. v10.8 clareou a célula vermelha e acrescentou uma faixa cinza sobre lentes/pintura. O friso original 2018 ainda estava em BASE, com textura escura. Usuário confirmou que tudo continuou escuro; versão substituída pela v10.9. Backups v10.7 em `backup/antes-v10.8/`.

Build em `local/v10.5/out-lamps-gray/`; validação passou (índices, referências de textura, roda idêntica à do Focus e chamadas BODY/TRUNK/WHEEL). Instalado para teste no jogo. GEOMETRY `E1E82EA663BFCB66BED0FFE2C1E092CB7E23A40540F82445089FA4C1703DB6B4`; TEXTURES `D867CD3FAB640A1C39EC1A84936044821015AE0059C249C2779CF296575C4719`. Aguardar avaliação visual.

# Continuar daqui

Estado, testes em andamento e pistas: [docs/CONTINUACAO-v10.md](docs/CONTINUACAO-v10.md). Leitor do banco de peças: `scripts/globalb_carparts.py`.

# v10.7 — lanternas na textura MISC já desenhada (06/10/2026)

Teste v10.6 não teve efeito, segundo o usuário: lanternas/refletores continuam ausentes. O nome padrão KIT00_BRAKELIGHT não resolveu; não atribuir a falha somente ao nome personalizado.

Instalado teste v10.7: lentes e refletores agora usam **MUSTANGGT_MISC + DULLPLASTIC**, a mesma combinação de peças visíveis da base. Os grupos iguais são unidos pelo escritor: as lentes externas entram no grupo MISC existente da BASE; internas usam MISC na TRUNK. Redirecionadas somente as UVs de cor para duas células livres, vermelho (13,14) e branco (14,14), grade 16×16 da folha 512×512. Células pintadas depois do redimensionamento e alinhadas aos blocos DXT1, evitando alterar pixels vizinhos. UVs das peças originais de MISC não passam de v=.75; células novas em v=.875–.9375.

Resultado visual: lanternas/refletores apareceram, mas escuros; a faixa transversal estava ausente. Substituído pelo v10.8 abaixo.

Verificações: mesmas posições/orientações de todas as faces de BODY/BASE/TRUNK/WHEEL da E; mesmas contagens 63.444 vértices / 60.777 triângulos; texels de MISC fora das duas células idênticos; outras texturas idênticas às da E (atlas personalizado removido). Banco intacto. Validação de arquivos passou.

- [ ] Usuário testar as quatro lanternas e refletores: aparecem vermelho/branco/vermelho opaco? Conferir também se o carro continua abrindo.
- Se continuar ausente mesmo dentro do grupo MISC visível, investigar caminho de renderização/atributos das faces, sem assumir que só um nome de textura ou transparência explique o problema.

GEOMETRY instalado `5F3C0750E5BF8FF8493AE9D168109D761DAFBCFC3B2B69F322A5388865347572`, TEXTURES `076DE305750BD6C89E99A974AA5D688A9CCFD8BBEBF7BC2796E8CCB425464146`. Backup v10.6 em `backup/antes-v10.7/`; E preservada em `backup/antes-v10.6/`. Variante `local/v10.5/out-lamps-misc/`. CARS no repositório ainda E; build prepara v10.7, pendente validação no jogo.

# v10.6 — lanternas ausentes: atlas padrão (06/10/2026)

Usuário enviou [captura](docs/in-game-v10.6/antes-lanternas-ausentes.png): os quatro vãos das lanternas mostram o interior; os refletores inferiores não estão vermelhos opacos. **A execução normal do teste E não aprovou as luzes.**

Todas as lentes novas usam `MUSTANGGT_SOLID_LAMPS` (DXT1 32×32), inclusive as milhas. Esse nome personalizado era lido pela prévia, sem validar o carregamento do jogo. Instalado teste com o atlas opaco vermelho/branco em **`MUSTANGGT_KIT00_BRAKELIGHT`**, entrada padrão já presente no pacote, em 256×256. A textura personalizada foi eliminada. Restante da antiga carcaça mantido para luz central/detalhes da cabine recebe a célula vermelha. Material DULLPLASTIC preservado.

Todas as faces de BODY/BASE/TRUNK/WHEEL comparadas: posições e orientação exatamente iguais às da versão E que abre. Conjunto ainda 63.444 vértices / 60.777 triângulos. Banco de peças intacto. Essa variante testa o carregamento/nome/formato do atlas, não é prova de causa confirmada antes de observar o jogo.

- [x] Resultado v10.6: nenhum efeito, mesmo cenário; não resolveu.
- Se ainda ausentes: investigar seleção de textura pelo shader e nome/material de grupo; não voltar à hipótese de fundo preto/transparência — o usuário confirmou que a geometria não é desenhada.

Instalado GEOMETRY `B8BC0C045CE7FD93E3A35D5576C3F4AE987DA15553CA522B33171AB8E24382E5` e TEXTURES `DD499C805E3EF4E46711F21218C0A5C8B31551A75B6106CF0CF405A402FE01DE`. Backup da E em `backup/antes-v10.6/`. Variante em `local/v10.5/out-lamps-standard/`. O repositório CARS mantém a E até validar essa mudança; script build já prepara o atlas padrão.

# v10.5 — versão funcional consolidada (06/10/2026)

**Teste E aprovado pelo usuário: "funcionou normalmente".** Tampa A com pintura reduzida para 8.000 triângulos e rodas habilitadas juntas. A configuração aprovada agora é o padrão do port 2018 (`trunk_paint_target: 8000` em `scripts/ports.py`). Build sem variáveis de diagnóstico reproduziu GEOMETRY/TEXTURES byte a byte iguais aos instalados. Geometria aprovada copiada para `CARS/MUSTANGGT`, log atualizado em `docs/build_log.json`. Não foi instalada outra malha após a aprovação.

- [x] Carro abre com carroceria, tampa e rodas juntas.
- [x] Roda exatamente igual à do 2012; lentes vermelhas/brancas opacas e milhas incluídas na versão funcional.
- [x] Reprodução da build padrão e validação dos arquivos.
- [ ] Conferência visual específica das lanternas/milhas, cidade e abertura da tampa na loja de som, se ainda não testadas. "Funcionou normalmente" confirma a execução; não equivale a aprovação visual detalhada de cada item.

Contagens do conjunto BODY + BASE + TRUNK + WHEEL: **63.444 vértices / 60.777 triângulos**. A tampa completa tem 10.328 triângulos; base 21.253, carroceria 20.582, roda 8.614. Versões maiores A original e D fecharam na mesma cadeia de carregamento. Não ficou comprovado um limite de 65.535: D também estava abaixo e fechou; manter o orçamento que passou até investigar memória/carregamento.

GEOMETRY aprovado: `4DD5BB956B26CC04FADFC482570E4FAA2A83F3DCFC9773CC8AEC316E79E9CE9C`. TEXTURES: `FBFAEA3378D306B2ABCF0227065B71B21CB3CAB940DEC9E680458D9F6CCE0DD8`. GlobalB: `0D9F51AF2F920E52F5C7AE62BC121F5FDFF1EDFC475F4F6E42A77CAFB3403E2B`, carroceria no layout aprovado + somente ids 10/28 do Focus. **Não aplicar a cópia integral de 270 peças**, que fechou. Instalação genérica pelo bat ainda precisa incorporar esse patch seletivo.

# v10.5 — teste E após fechamento do D (06/10/2026)

Teste D **reprovado**: usuário informou travamento e fechamento. Evento Windows às 19:49:47; dump `SPEED2.EXE.30952.dmp`: `0x80000003` em `0x43BD50`, sequência `0x63A265 → 0x63ADAC → 0x63B25D → 0x610A40`, igual aos fechamentos anteriores. Backup do D e dump em `backup/v10.5-teste-D-fechamento/`. O limite simples de 65.535 vértices/triângulos não explica sozinho: D estava abaixo de ambos. Memória/orçamento de carregamento ainda não comprovados.

Teste C restaurado durante a preparação. Agora instalado **teste E**, ainda com tampa e roda juntas: pintura da tampa A reduzida para 8.000 triângulos; tampa completa 10.328 triângulos / 10.569 vértices; conjunto **63.444 vértices / 60.777 triângulos**. Mantém mais geometria que a tampa B do C (8.563 triângulos), mas menos que a tampa do D. Lanternas, rodas, base, carroceria e texturas mantidas. Variante `local/v10.5/out-trunk-A8000/`; construir com `BUILD_TRUNK_PAINT_TARGET=8000`.

- [x] Usuário confirmou: "funcionou normalmente". Acabamento detalhado não descrito.
- Se falhar: restaurar C (LOD B) como configuração funcional e investigar carregamento antes de outra tentativa de aumentar detalhe. Não continuar tratando 65.535 como limite suficiente.

GEOMETRY instalado `4DD5BB956B26CC04FADFC482570E4FAA2A83F3DCFC9773CC8AEC316E79E9CE9C`; banco tampa+roda inalterado (`0D9F51AF…403E2B`). Teste C preservado em `backup/v10.5-teste-C/` e `local/v10.5/out-trunk-B/`.

# v10.5 — teste D: tampa A reduzida, roda original (06/10/2026)

Resposta do usuário ao teste C: "ok, próximo", interpretada como combinação tampa B + rodas funcionando. Essa interpretação foi informada na conversa. Backup desse estado em `backup/v10.5-teste-C/`.

Instalado teste D: tampa extraída do **LOD A**, com pintura reduzida de 15.340 para 10.999 triângulos (QEM com bordas/costuras preservadas pelo decimador). A tampa completa tem 13.327 triângulos e 12.445 vértices; teste C tinha 8.563 / 9.174. Lanternas não foram decimadas. Base, carroceria, roda e texturas comparadas e idênticas às originais. O conjunto BODY + BASE + TRUNK + WHEEL tem **65.320 vértices e 63.776 triângulos**, abaixo de 65.535; hipótese do limite agregado ainda não isolada de um limite de memória.

- [x] Resultado: travou e fechou. Teste D reprovado.
- Se fechar: retornar ao teste C e investigar orçamento/memória; estar abaixo de 65.535 não bastou.
- Se abrir: comparar visualmente A reduzido × B antes de consolidar a versão final.

Variante em `local/v10.5/out-trunk-A11000/`, produzida com `BUILD_TRUNK_PAINT_TARGET=11000`. GEOMETRY instalado `E91EC3E9FB4751370D76C7132F6ECCF0E657CD04895917DF2AE12B819644B73A`; banco permanece `0D9F51AF2F920E52F5C7AE62BC121F5FDFF1EDFC475F4F6E42A77CAFB3403E2B` (tampa e roda habilitadas). Repositório mantém a geometria A original, sem redução; teste ainda não consolidado. [Prévia D](docs/in-game-v10.5/previa-teste-D.png).

# v10.5 — teste C: tampa e roda juntas, tampa LOD B (06/10/2026)

**Teste B aprovado pelo usuário: rodas OK.** A tampa (teste A) e as rodas (teste B) funcionam isoladamente. A combinação da tampa A com roda fecha.

Hipótese em teste: limite agregado de 16 bits. Contagens reais dos buffers compilados de BODY + BASE + TRUNK + WHEEL: 67.856 vértices e 68.117 triângulos na versão final, ambas acima de 65.535. Abaixo do limite em cada teste isolado. Isso é correlação, ainda não demonstra um limite real do motor.

Instalado teste C: **tampa e roda habilitadas juntas**, mesma base, carroceria, roda e texturas (comparadas byte a byte). Só a pintura da tampa usa o LOD B da fonte em vez do A. Contagens da tampa: 9.174 vértices / 8.563 triângulos; conjunto 62.049 vértices / 59.012 triângulos. Lanternas opacas vermelhas/brancas mantidas. O teste reduz simultaneamente vértices/triângulos e memória da tampa; se abrir, não distinguirá qual desses limites é a causa.

- [x] Usuário respondeu "ok, próximo"; tratado como teste C aprovado, conforme comentário na conversa.
- Se abrir: investigar qual limite agregado/memória causa o fechamento antes de decidir a qualidade final da tampa.
- Se fechar: descartar a hipótese simples de soma >65.535; investigar interação/carregamento das duas peças.

Banco instalado: `0D9F51AF2F920E52F5C7AE62BC121F5FDFF1EDFC475F4F6E42A77CAFB3403E2B` (tampa + roda). GEOMETRY instalado: `72A1B07232ADB385EBE9A8125FC0A78C24E5D10D0AB384BF0A77CE96DEE4C415`. Variante em `local/v10.5/out-trunk-B/`; construir com `BUILD_TRUNK_LOD=B`. A geometria original no repositório permanece com tampa A. Backup do teste B aprovado em `backup/v10.5-roda-aprovada/`.

# v10.5 — teste B: só a roda habilitada (06/10/2026)

**Teste A aprovado pelo usuário: a tampa foi exibida.** Banco aprovado preservado em `backup/v10.5-tampa-aprovada/GLOBAL/GlobalB.lzc`.

Instalado teste B: carroceria e roda habilitadas; tampa temporariamente desabilitada. Geometria/texturas finais intactas. Variante gerada da carroceria aprovada, copiando somente o id 28 do Focus. Arquivo `local/v10.5/GlobalB.wheel.lzc`; SHA do banco instalado `A4B190F056DC09876B80C0F22DAA64CE9936DD4E62E0414089B966E8014A37EC`.

- [x] Usuário testou: rodas OK, sem fechamento.
- Se fechar: a chamada da roda basta para reproduzir o erro; investigar aro/tabela/atributos e carregamento do slot. A malha já é idêntica à roda do 2012.
- Se abrir: a combinação tampa+roda é o fator, investigar orçamento/gerenciamento de recursos; não concluir que a roda sozinha está defeituosa.

# v10.5 — teste A: só a tampa habilitada (06/10/2026)

A v10.5 com tampa e roda habilitadas fechou ao mostrar o Mustang. Dump `SPEED2.EXE.27412.dmp`, 19:38: exceção `0x80000003` em `0x43BD50`, retorno `0x63A265` e sequência `0x63ADAC → 0x63B25D → 0x610A40`; idênticos ao dump das 18:01 (`33184`, cópia integral do layout que travou). A falha ocorre numa verificação interna na cadeia de carregamento de recursos; o dump não nomeia a peça nem comprova a causa exata.

Instalado **teste A**: geometria e texturas finais da v10.5 intactas, carroceria e tampa habilitadas, roda com a tabela anterior que não chama `FRONT_WHEEL_A`. Só um byte do GlobalB mudou em relação à variante que fechou (offset 10295894, índice de tabela do id 28). SHA do GlobalB: `59E3BC4BA1ACEDAFE7F52B1905B0203FC36953CFF7634824B67B03F1D44FDC8D`. Backup do banco e do dump em `backup/v10.5-fechamento/`.

- [x] Usuário testou o Mustang: a tampa foi exibida, sem fechamento.
- Se abrir e mostrar a tampa: a ativação da roda é o fator isolado; investigar tabela/atributos do slot e dimensões de aro antes de reativá-la.
- Se fechar: testar só a carroceria com a geometria atual; se abrir, investigar a chamada da tampa. Se ainda fechar, comparar a geometria atual com a anterior aprovada, com o mesmo banco.

# v10.5 — TODO do 2018, imagens do usuário (06/10/2026)

A v10.4 com só a carroceria foi aprovada nas imagens: laterais, portas e teto aparecem. Referências guardadas em [traseira](docs/in-game-v10.5/antes-traseira.png) e [frente](docs/in-game-v10.5/antes-frente.png).

- [x] Preparar a tampa: a tabela do Mustang não tinha modelo. Só o id 10 recebe a tabela `FOCUS_KIT00_TRUNK_A`, com prefixo do Mustang.
- [x] Preparar as rodas: só o id 28 recebe a chamada `MUSTANGGT_KIT00_FRONT_WHEEL_A`. A malha é copiada do 2012 instalado: buffers de vértices e índices idênticos; texturas RIM/TIRE também idênticas. O banco muda apenas os dois índices de tabela (três bytes). Aro/performance continuam como estavam no teste da carroceria.
- [x] Preparar as lanternas: quatro conjuntos (esquerda/direita × carroceria/tampa), com anel vermelho opaco e fundo branco opaco seguindo o contorno da lente. Atlas DXT1 sem transparência, material DULLPLASTIC. Miolo cromado removido das peças de luz e da base; lábios pintados que atravessavam o fundo branco também removidos. Parte externa fica na BASE, interna na TRUNK. Refletores baixos continuam vermelhos. Método do item 27 do MW (fundo sólido por trás da lente), adaptado para o 2018, em `scripts/solid_lamps.py`.
- [x] Preparar os faróis de milha: LOD A na BASE, carcaça orientada para fora e lente branca opaca preenchendo o contorno. Sai o conjunto antigo de LOD C da carroceria; removidas peças da base que atravessavam a lente.
- [x] Validar arquivos reabertos: limite de índices, referências de textura, alfa 255, igualdade exata da roda do 2012 e chamadas BODY/TRUNK/WHEEL. `scripts/validate_2018.py` passou também nos arquivos instalados.
- [ ] Testar no jogo: tampa, quatro rodas, lentes vermelhas/brancas sem cromado e os dois faróis de milha. Conferir garagem e cidade, além de abrir o porta-malas na loja de som. **Ainda não aprovado no jogo.**

Instalado para teste com backup em `backup/antes-v10.5/`. O 2012 não foi editado. A build usa o ZIP aprovado do MW e a roda do `CARS/FOCUS/GEOMETRY.BIN`; fontes do MW intactas. Variantes só da tampa e da tampa+roda em `local/v10.5/GlobalB.trunk.lzc` e `local/v10.5/GlobalB.lzc` para diagnóstico se houver fechamento.

Orçamento final: carroceria 20,582, porta-malas 17,668, base 21,262 e roda 8.614 triângulos; todas abaixo de 21.500. [Prévia de bancada](docs/in-game-v10.5/previa-bancada.png); a imagem não comprova o que o slot desenha no jogo.

# v10.4 — lista de peças do Mustang no GlobalB (06/10/2026)

Os dois testes da v10.3 falharam. Decifrado o banco de peças do `GlobalB` (`0x80034602`): registros de 14 bytes em `0x34604` (hash do nome `<CARRO>_<PEÇA>`, id da peça, sub-id, flag, índice do carro na lista `0x3460B`, dois índices de atributos, índice da tabela de modelo), tabelas de modelo de 36 bytes em `0x3460A` (`<CARRO>` + texto + entrada por LOD A–D e mais quatro), textos em `0x34606` (deslocamento × 4).

- O Mustang personalizado tinha deixado vazia a entrada do LOD A em quase todas as peças do `MUSTANGGT` (carroceria, roda, para-choques, capô...) e apagado a do porta-malas. O jogo pedia `MUSTANGGT_KIT00_A`. Corrigido com `scripts/globalb_parts.py`: as 270 peças do Mustang passam a usar as tabelas das peças do Focus (153 índices mudaram). As tabelas são compartilhadas entre carros e não foram editadas.
- A v10.3 do 2018 (LOD B/C com a mesma malha) foi desfeita: no layout do Focus o jogo pede só o A.
- [x] Testar o 2018 no Mustang: **o jogo trava ao mostrar o carro** com as 270 peças no layout do Focus. Em teste: só a carroceria (ids 5 e 6), `GlobalB` `E5A03095…`.
- [ ] Depois: o 2012 (faróis, faróis de milha e lanternas). No layout do Focus `KIT00_HEADLIGHT` e `KIT00_BRAKELIGHT` não têm LOD A; as luzes estão dentro da carroceria e do porta-malas.

# v10.3 — teste de estrutura das peças (06/10/2026)

Teste da v10.2: no 2012 faróis, faróis de milha e lanternas não existem (vê-se o interior pelos buracos), na garagem, na corrida rápida, na loja e no mundo aberto. O 2018 no Mustang, sem vinil, continua sem a pintura das laterais e sem rodas.

- 2012: as luzes eram os únicos grupos repetidos dentro da carroceria e do porta-malas (lado direito e esquerdo com a mesma textura e o mesmo material, em grupos separados). Na v9, que o jogo desenhou inteira, cada peça tinha um grupo por textura e material. Agora os grupos iguais são unidos: carroceria e porta-malas ficam com 3 grupos, como na v9.
- 2018: os carros originais têm LOD B e C de carroceria, porta-malas e roda; o slot do Focus (configurado pelo Escort) só usa o A. O Mustang desenha a base (só A nos nossos arquivos) mas não a carroceria, o porta-malas e as rodas. Teste: as mesmas malhas também com os nomes `_B` e `_C` (`lod_alias` em `ports.py`).
- [ ] Resultado dos dois testes.

# v10.2 — faróis do 2012 e faces repetidas (06/10/2026)

Teste da v10.1 (carros salvos em "Selec. Carro Personalizado"): o 2012 abriu inteiro, mas com faróis e faróis de milha como buracos pretos; o 2018 no Mustang mostrou capô, frente do teto, vidros, grade, placa e faróis, sem a pintura das laterais e sem rodas.

- 2012: a carcaça do farol (e do farol de milha, na mesma peça do MW) usa em 63 % da área uma célula preta da folha, que no MW o shader de lâmpada ilumina. A cópia UG2 da folha troca essa célula por cromado escurecido (`tex_cells` em `ports.py`).
- Os dois: tiradas as faces repetidas viradas para dentro na base, nas carcaças das luzes e no interior (2012: 864 em `MISC`, 563 em `LOGO`, 481 na pintura da base, 3.429 no interior). O interior ganhou detalhe com o orçamento liberado.
- [ ] 2018 no Mustang: os faróis estão na mesma peça da pintura lateral (`KIT00_BODY_A`) e aparecem, então a peça é desenhada e só a pintura dela some. A pintura da `BASE_A` (capô) aparece. Suspeita: o vinil do carro salvo, que o jogo aplica só na carroceria. Testar o Mustang de série e o salvo sem vinil.

# v10.1 — correção do teste da v10 (06/10/2026)

Teste da v10: o 2012 apareceu sem faróis, lanternas, faróis de milha e detalhe dos escapamentos; o 2018 no Mustang mostrou só o capô e o para-brisa.

- Os dois `TEXTURES.BIN` tinham o mesmo cabeçalho herdado do MW (nome vazio, hash `FFFFFFFF`). O v9 era o único assim no jogo. Agora cada pacote tem a identidade dos carros originais (`CarTemplateTextures_<SLOT>.tpk`). A geometria do 2018 é a mesma da v10: só a textura mudou, para isolar a causa.
- 2012: voltaram as lentes e as saias baixas com as duas faces (como na v9); `lens: outward` e `valance: inward` tiravam faces que o jogo precisa. Para caber, o para-choque traseiro passou a LOD B e a base decima mais (0,75).
- O Mustang personalizado (mod de 2019 que ocupava o slot) não foi doador: nada dele entra na build. O registro `MUSTANGGT` do `GlobalB` foi comparado com o original do jogo e só difere nas tabelas que o Nikki reescreveu em todos os carros.

- [ ] Testar de novo os dois carros.

# v10 — os dois Fusion reexportados da release v2.7 do MW (06/10/2026)

Instalados para teste: 2018 em `CARS/MUSTANGGT`, 2012 em `CARS/FOCUS`, `GlobalB.lzc` com os dois registros (SHA no README). Backup do estado anterior em `backup/antes-v10-2026-10-06/`. Orçamento e regras novas em [docs/PORTAR-PARA-NFSU2.md](docs/PORTAR-PARA-NFSU2.md), seção 8.

- [ ] **Testar o 2018 no slot do Mustang**: seleção, garagem, cidade. Conferir se a tampa do porta-malas aparece (o mod de Mustang instalado antes não tinha `TRUNK_A`), lanternas vermelhas, rodas nos arcos e um vinil.
- [ ] **Testar o 2012 no slot do Focus**: faróis LOD D, lanternas, refletores pequenos sobre o escape, grade e para-choque, tração dianteira no menu de desempenho.
- [ ] Se o 2018 abrir sem a tampa: medir o que o slot `MUSTANGGT` desenha e mover a tampa para uma peça desenhada.
- [ ] `release/instalar.bat` instala só o 2018; falta a opção do 2012.

Peças: 2018 carroceria 21.228 · `TRUNK_A` 18.021 · `BASE_A` 21.236. 2012 carroceria 21.402 · `TRUNK_A` 21.020 · `BASE_A` 21.254. Logs em `docs/build_log.json` e `docs/build_log_2012.json`.

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
