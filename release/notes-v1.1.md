# v1.1 — Fusion 2018 AWD e Fusion 2012 FWD

Uma release com dois ZIPs separados, como no projeto MW2005. O formato público passa a ser `vX.X`; a tag/release antiga v1.0.1 foi substituída.

- **Fusion 2018 AWD:** substitui o Mustang GT. Inclui tampa, rodas do 2012, lentes vermelhas/brancas opacas, refletores e friso original branco. Acrescenta o prolongamento do friso nas lanternas externas e o branco abaixo dele nas lanternas da tampa.
- **Fusion 2012 FWD:** substitui o Focus. Mantém o port atual, com tração dianteira e roda compartilhada.
- Instalador de cada pacote aceita GlobalB JDLZ ou descompactado, preserva backups e aplica os ajustes do slot correspondente. No Mustang, altera somente as tabelas de peças 5/6/10/28.
- README atualizado com referências reais, capturas, prévias compiladas e aprendizados. Correção pontual do copyright da tela inicial disponível no código-fonte.

**Estado da validação:** a base v10.9 do 2018 foi aprovada no jogo. O prolongamento do friso e o branco inferior da v10.10 aguardam confirmação visual. A v1.1 é publicada sem aguardar a finalização do friso; os próximos ajustes serão publicados como v1.2, v1.3 e assim por diante. No 2012, a exibição das luzes ainda está pendente; seu pacote é um port de desenvolvimento. Os limites/índices/referências do 2018 foram validados e o patch do instalador foi comparado byte a byte com os scripts Python, incluindo o banco original JDLZ e Windows PowerShell.

## Instalar

Extraia o ZIP desejado e execute `instalar.bat` com o jogo fechado. Mantenha `globalb_patch.ps1` junto dele. Para instalar os dois carros, execute o instalador de cada pacote. Não exige Python ou Nikki. O banco e os arquivos de idioma completos do jogo não são distribuídos.

`SHA256SUMS.txt` verifica os arquivos de download; `SHA256SUMS-conteudo.txt` registra os arquivos dentro dos ZIPs. Cada ZIP também contém seu próprio manifesto.
