---
name: publish-release
description: >-
  Publica release do fusion-nfsu2 no GitHub: push da branch, calcula a próxima
  versão (última release + 1), usa o título do último commit, cria tag/release
  com artefatos em local/release-vX.Y/, marca como latest e remove tags e
  releases anteriores. Use quando o usuário pedir publicar, empurrar release,
  criar tag, gh release, ou invocar publish-release.
disable-model-invocation: true
---

# Publicar release (fusion-nfsu2)

Fluxo único: push → próxima versão + título do commit → tag/release → apagar antigas.

## Quando usar

Somente quando o usuário pedir explicitamente (ou invocar esta skill). Não publicar sozinho.

## Versão e título (automáticos)

Não pedir versão nem título. O script calcula:

**Versão** — última release no GitHub (`gh release list`) + 1 no componente final (`v1.4` → `v1.5`). Se não houver release no GitHub, usa a maior pasta/notes local `vX.Y` e soma 1. Se não houver nada, começa em `1.0`.

**Título** — assunto do último commit: `git log -1 --pretty=%s`.

A pasta e as notes devem existir para a **versão nova**:

```
local/release-vX.Y/   # ex.: local/release-v1.5/
release/notes-vX.Y.md
```

## Artefatos obrigatórios

```
local/release-vX.Y/Fusion2018_AWD_NFSU2.zip
local/release-vX.Y/Fusion2012_FWD_NFSU2.zip
local/release-vX.Y/instalar.bat
local/release-vX.Y/globalb_patch.ps1
local/release-vX.Y/SHA256SUMS.txt
local/release-vX.Y/SHA256SUMS-conteudo.txt
release/notes-vX.Y.md
```

Se faltar algum para a versão calculada, parar e informar. Não inventar ZIP nem notes.

## Checklist

```
Progresso:
- [ ] 1. Resolver gh
- [ ] 2. Calcular próxima versão + título do último commit
- [ ] 3. Validar artefatos/notes da versão nova
- [ ] 4. Push dos commits já existentes (ignorar WIP)
- [ ] 5. Criar release com --latest
- [ ] 6. Apagar todas as releases/tags anteriores
- [ ] 7. Confirmar URL e lista final
```

## Passo 1 — gh

Rodar na raiz do repo (`fusion-nfsu2`).

1. Se `gh` estiver no PATH, usar.
2. Senão, baixar portátil (sem admin):

```powershell
$ghDir = Join-Path $env:TEMP 'gh-cli'
New-Item -ItemType Directory -Force -Path $ghDir | Out-Null
$zipPath = Join-Path $ghDir 'gh.zip'
$release = Invoke-RestMethod -Uri 'https://api.github.com/repos/cli/cli/releases/latest'
$asset = $release.assets | Where-Object { $_.name -match 'windows_amd64\.zip$' } | Select-Object -First 1
Invoke-WebRequest -Uri $asset.browser_download_url -OutFile $zipPath
Expand-Archive -Path $zipPath -DestinationPath $ghDir -Force
$gh = (Get-ChildItem -Path $ghDir -Recurse -Filter 'gh.exe' | Select-Object -First 1).FullName
```

3. Confirmar auth: `& $gh auth status` (precisa scope `repo`).

## Passo 2 — push

Esta skill **não faz commit**. Trabalhos em progresso (working tree suja) **não interferem**: não bloquear, não avisar para limpar, não descartar, não staged/unstaged — apenas ignorar.

1. Conferir o último commit (título da release): `git log -1 --pretty=%s`.
2. Push só do que já está commitado:

```powershell
git push -u origin HEAD
```

Se o push falhar por auth/rede, parar — sem criar release desencontrada do remoto.

## Passo 3 — criar release e limpar antigas

```powershell
.cursor/skills/publish-release/scripts/publish-release.ps1 -Push
```

O script:

1. Lê a última release no GitHub e define a próxima (`v1.4` → `v1.5`)
2. Título = `git log -1 --pretty=%s`
3. Valida `local/release-vX.Y/` + `release/notes-vX.Y.md`
4. Resolve `gh` (PATH ou `%TEMP%\gh-cli`)
5. Cria a release com os 6 artefatos, `--notes-file` e `--latest`
6. Apaga todas as **outras** releases/tags (as anteriores)
7. Imprime URL e `gh release list`

Overrides opcionais (raros): `-Version 1.5`, `-Title "..."`, `-SkipPush`, `-GhPath`.

## Regras

- **Não commitar.** Não `git add`, não `git commit`, não `git stash`, não descartar mudanças locais.
- WIP é irrelevante para o publish: seguir com push + release mesmo com working tree suja.
- Uma release pública por vez: a nova é `--latest`; as anteriores saem (tag + release).
- Não apagar a release que acabou de criar.
- Não usar `pint` / Laravel Sail (irrelevante neste repo).
- Responder em português com versão, título (do commit) e URL final.
- Histórico git antigo permanece; só some a release/tag no GitHub.

## Exemplo

Com `v1.4` no GitHub e commit `v12.1: orient paint faces...`:

```text
Versão: v1.5
Título: v12.1: orient paint faces...
Artefatos: local/release-v1.5/ + release/notes-v1.5.md
```
