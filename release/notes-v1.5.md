# v1.5 — Fusion 2018 AWD e Fusion 2012 FWD

As carrocerias dos dois Fusion ficaram lisas e uniformes, sem o craquelado na lateral, nas portas, nos para-lamas traseiros e perto dos faróis. O resultado foi aprovado no jogo.

- **Normais do LOD A:** a pintura decimada passa a usar as normais originais do modelo de alta resolução do MW. As faces são orientadas por elas, e a exportação deixa de substituí-las pela média das faces, que invertia parte delas e criava manchas escuras.
- **Frente suavizada:** capô, para-choque e para-lamas perto dos faróis recebem suavização das normais, preservando os vincos.
- **2012, traseira:** tampa e para-choque passam a vir do LOD A, decimados como a tampa do 2018. O rebaixo da placa foi fechado. A pintura plana (lateral e para-lama traseiro) passa a ser decimada a partir do LOD A.
- **2012, lanternas:** a lente vermelha tem uma única camada, voltada para fora. Some a mancha escura causada pela cópia interna.
- **2018, refletores inferiores:** o mesmo acabamento aprovado no 2012, com uma camada externa e iluminação uniforme.
- **Memória:** texturas e triângulos dentro dos limites da v1.4; o 2018 abre normalmente com o 2012 instalado.

## Instalar

Extraia o ZIP desejado e execute `instalar.bat` com o jogo fechado. Mantenha `globalb_patch.ps1` junto dele. O 2018 substitui o Mustang GT; o 2012 substitui o Focus.

`SHA256SUMS.txt` verifica os downloads; `SHA256SUMS-conteudo.txt` registra os arquivos dentro dos ZIPs.
