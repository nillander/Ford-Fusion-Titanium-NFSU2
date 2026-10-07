# Continuação para o Codex — Fusion NFSU2 (07/10/2026)

Este é o estado do projeto e o que precisa continuar. Leia antes de mexer. O histórico detalhado está em `TODO.md` (mais recente no topo) e nos `docs/*.md`.

## Estado atual

- **Publicado no GitHub:** v1.7 (tag e release). 2018 v12.2 no slot `MUSTANGGT` e 2012 v12.6 no slot `FOCUS`, os dois aprovados no jogo.
- **Instalado no jogo agora:** exatamente os BIN da v1.7, iguais a `CARS/MUSTANGGT` e `CARS/FOCUS` do repositório (conferir com `sha256sum`).
- **Último teste, que falhou:** v12.8, tampa do 2018 decimada para 10.000 faces em vez de 6.000. O jogo travou e fechou ao visualizar o 2018. Foi restaurado o BIN da v1.7, `trunk_paint_target` voltou a 6.000 em `scripts/ports.py`, e os arquivos que falharam estão em `backup/falha-v12.8/`.
- **Commits locais ainda não enviados:** v12.7, a reversão da v12.7, v12.8, `export_obj.py`, a reversão da v12.8 e este documento. Fazer push.

## Ambiente

- O repositório fica em `C:\Users\nillander\NoDocuments\fusion-nfsu2`. O jogo fica em `...\NoDocuments\Need for Speed Underground 2`.
- Instale com o jogo fechado, copiando `GEOMETRY.BIN` e `TEXTURES.BIN` para `CARS/<SLOT>/`, sempre com backup em `backup/antes-<versão>/CARS/<SLOT>/`.
- Os BIN de `CARS/` estão em Git LFS (o `TEXTURES.BIN` do Mustang não está). Nos commits, use `core.autocrlf=true`.
- Commits: assunto curto em inglês para trabalho; `Publica vX.Y: <resumo>` para release, porque esse assunto vira o título da release.

## Como construir

Em cada pasta de trabalho já existem a extração do MW (`mw/`, `mw_parts.pkl`, `texdump/`):

```
cd local/v10.5          && python ../../scripts/build.py out-<versão> 2018
cd local/reflectors-2012 && python ../../scripts/build.py out-<versão> 2012
```

As configurações de cada carro ficam em `scripts/ports.py`. Para testar parâmetros sem editar o arquivo, use `BUILD_PORT_OVERRIDE='{"chave": valor}'`. `BUILD_DRY=1` só imprime o orçamento.

Prévias, todas lendo os BIN compilados:

- `scripts/preview_paint.py GEOMETRY.BIN saida.png [az,el,escala,cx,cy,cz ...]`: listras de ambiente refletidas pelas normais da pintura. Exagera ondulações e não reproduz o shader do jogo.
- `scripts/preview_tail.py GEOMETRY.BIN TEXTURES.BIN prefixo`: traseira com texturas.
- `scripts/preview.py`: seis vistas.
- `local/v12-tests/tailzoom.py`: lanterna de perto, fundo amarelo.

Mostre as prévias ao usuário antes de instalar.

## Limites e regras aprendidos (não violar)

1. **Triângulos por peça:** no máximo 21.500 por sólido (índices de 16 bits). Hoje: 2018 com BODY 20.582, TRUNK 7.473 e BASE 21.272; 2012 com BODY 20.957, TRUNK 20.855 e BASE 21.299.
2. **Memória dos carros é o limite real.** O jogo fecha (exceção 0x80000003) quando o carro fica mais pesado, mesmo abaixo do limite de triângulos. Já fechou nestes casos:
   - v10.14: tampa do 2018 mais pesada;
   - v11: 2012 com cerca de 225 KB a mais de texturas vinculadas, o que fazia o 2018 fechar;
   - v12.8: tampa do 2018 com 10.000 faces, mesmo com as texturas 213 KB mais leves que na v10.14.

   Qualquer aumento de geometria ou textura precisa ser compensado em outro lugar. Teste sempre os dois carros.
3. **Nomes de textura:** o UG2 só vincula as texturas cujo nome ele monta: `%s_MISC`, `%s_SIDELIGHT`, `%s_DOOR_HANDLE`, `%s_CENTRE_BRAKELIGHT` e `<TEXTURE_NAME da lâmpada>_GLASS_OFF` (`FOCUS_KIT00_HEADLIGHT_GLASS_OFF`). Qualquer outro nome não é desenhado. Ver `tex_alias` em `ports.py` e `docs/LUZES-2012-v11.md`. Texturas vinculadas ficam residentes na memória.
4. **Cores sólidas:** as cores opacas das lâmpadas usam células livres de `MISC` com `DULLPLASTIC` (`solid_lamps.py`).
5. **Nada de faces opostas sobrepostas:** o jogo desenha as duas faces; uma cópia interna sobre a externa gera manchas. Use uma camada só, voltada para fora (`face_out`, `drop_inward_twins`, `lens_brake: outward`).
6. **Pintura:**
   - normais transferidas do LOD A (`normals_from_A`) e faces orientadas por elas (`orient_paint`);
   - a correção de normais da exportação não substitui as normais da pintura;
   - isso tirou o craquelado grosso e foi aprovado (v12/v12.1/v12.2).
7. **O que falhou e não deve ser repetido:**
   - relaxar as normais em grandes áreas da malha decimada (v12.1 na traseira, v12.7 em tampa, para-choque e portas): no jogo fica com aspecto de baixa resolução e as manchas continuam. Só o relaxamento na frente, perto dos faróis, ficou;
   - aumentar a tampa do 2018 (v12.8): o jogo fecha.
8. **Lanternas do 2012 (v12.3–v12.6):**
   - lente opaca vermelha e branca conforme a textura do MW;
   - folhas atrás de cada lanterna;
   - rachaduras da lente fechadas com quadrados de 1 mm (`fill_gaps`);
   - centro branco puxado para uma superfície quadrática (`flatten_quadratic`).
9. **Sessões em paralelo:** uma sessão do Cursor já editou os mesmos arquivos ao mesmo tempo. Antes de começar, confira `git status` e as datas de modificação.

## Pendências

1. **Manchas escuras nas traseiras dos dois carros, e traseira e lateral do 2012 com aspecto quadrado e irregular.**
   - **Causa:** as cores de vértice da pintura são brancas. As manchas são o reflexo do ambiente escuro da garagem nas ondulações da superfície. Elas vêm da decimação forçada pelos limites: o 2018 tem a tampa com 6.000 faces, a partir de 15.340; o 2012 tem a carroceria com 15.200, a partir de 57.597, e a traseira com 14.800, a partir de 20.483.
   - **Caminho:** mais resolução sem aumentar a memória. Isso exige tirar triângulos ou bytes de outras partes:
     - carcaça das lanternas do 2012 (cerca de 3.800 triângulos);
     - interior e motorista na BASE;
     - textura `FOCUS_DRIVER` / `MUSTANGGT_DRIVER`, que não é vinculada e provavelmente é desperdício;
     - LOGO e INTERIOR a 512 px.

     Depois mover o orçamento liberado para a pintura, um passo de cada vez, testando se o jogo fecha.
2. **Hipótese NFS-CarToolkit 3.1** ([anúncio](https://nfs-tools.blogspot.com/2020/07/nfs-cartoolkit-v31-released.html)):
   - é uma ferramenta Windows que converte entre OBJ/Z3D e UG/UG2/MW/Carbon/ProStreet/Undercover;
   - o teste é verificar se o compilador dela gera um UG2 com a malha LOD A completa, repartida de um jeito que o jogo carregue sem fechar. O limite de memória continua valendo;
   - OBJs prontos em `local/cartoolkit/` (`scripts/export_obj.py`): `fusion2012_mw_body_A.obj`, `fusion2018_mw_body_A.obj` e os BIN atuais;
   - se funcionar, comparar o tamanho e a divisão dos sólidos gerados com os nossos, e copiar a estratégia para o `build.py`.
3. **Push** dos commits locais.
4. **Menores:** a textura `FOCUS_DRIVER` não é vinculada, então o piloto provavelmente não aparece. Pode virar `LICENSE_PLATE` ou ser removida para liberar memória.

## Parecer final (Claude, retomada das 02:32)

Não mudei nada no jogo, porque o teste da tampa do 2018 com 10.000 faces ainda dependia do usuário. Esse teste depois fechou o jogo e foi revertido. Avaliei o NFS-CarToolkit 3.1: é uma ferramenta Windows que converte carros entre OBJ/Z3D e vários NFS, incluindo o UG2. Vale testar se ela gera o carro do UG2 com a malha detalhada do MW inteira, sem simplificação, e se o jogo aceita. É a simplificação que causa a geometria quadrada e irregular, então isso resolveria o problema na origem; o limite de memória continua valendo. Não foi possível rodá-la desta sessão (shell Linux, sem executar programas de terceiros); o teste precisa ser feito no Windows. Ficaram pendentes as manchas escuras nas traseiras e o push dos commits locais.
