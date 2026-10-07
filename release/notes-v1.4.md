# v1.4 — Fusion 2018 AWD e Fusion 2012 FWD

As luzes do Fusion 2012 foram aprovadas no jogo, e o farol de milha do Fusion 2018 agora é desenhado como o farol principal.

- **Texturas vinculadas pelo jogo:** o UG2 só usa as texturas de carro cujos nomes ele próprio monta (`%s_MISC`, `%s_SIDELIGHT`, `%s_CENTRE_BRAKELIGHT`, `<lâmpada>_GLASS_OFF`...). As folhas das lâmpadas tinham outros nomes e eram ignoradas. Agora são renomeadas, sem mudar pixels nem geometria.
- **2012:** faróis, faróis de milha e lanternas visíveis. Os refletores inferiores ficaram com uma única camada externa e normal plana, o que eliminou o vermelho escuro.
- **2018:** o farol de milha usa a carcaça e a lente reais (LOD B, 570 triângulos, contra 808) no lugar da folha branca plana.
- **Memória:** as texturas vinculadas ficam residentes. Lentes em 128 px, emblemas em 256 px e folhas sem uso removidas mantêm o total abaixo do da v1.3. Com o 2012 sem essa redução, visualizar o 2018 fechava o jogo.

## Instalar

Extraia o ZIP desejado e execute `instalar.bat` com o jogo fechado. Mantenha `globalb_patch.ps1` junto dele. O 2018 substitui o Mustang GT; o 2012 substitui o Focus.

`SHA256SUMS.txt` verifica os downloads; `SHA256SUMS-conteudo.txt` registra os arquivos dentro dos ZIPs.
