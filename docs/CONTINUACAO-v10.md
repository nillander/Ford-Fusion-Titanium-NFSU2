# Continuação — v10 (reexportação da v2.7 do MW), estado em 06/10/2026 18:05

Leia antes de mexer: [PORTAR-PARA-NFSU2.md](PORTAR-PARA-NFSU2.md) (seções 8 e 9), [TODO.md](../TODO.md) (v10 a v10.4).

## O que está instalado no jogo agora

| Arquivo | SHA-256 | O que é |
| --- | --- | --- |
| `CARS/MUSTANGGT/GEOMETRY.BIN` | `451516A9…D681CA` | Fusion 2018 da v2.7, divisão da v9 (= `CARS/MUSTANGGT` do repositório) |
| `CARS/MUSTANGGT/TEXTURES.BIN` | `D57805B1…E91170` | identidade `CarTemplateTextures_MUSTANGGT.tpk` |
| `CARS/FOCUS/GEOMETRY.BIN` / `TEXTURES.BIN` | ver README | Fusion 2012 v10.3 (grupos unidos) |
| `GLOBAL/GlobalB.lzc` | `E5A03095…DFC3B42` | **variante de teste**: registros `FOCUS` (2012 FWD) e `MUSTANGGT` (2018 AWD) de `globalb_patch.py` + **só** carroceria e carrocerias largas do Mustang no layout do Focus (`globalb_parts.py … FOCUS MUSTANGGT 5,6`) |

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
