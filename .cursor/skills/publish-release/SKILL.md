---
name: publish-release
description: >-
  Publica release do fusion-nfsu2 no GitHub: push da branch, cria tag/release
  com os artefatos em local/release-vX.Y/, marca como latest e remove tags e
  releases anteriores. Use quando o usuário pedir publicar, empurrar release,
  criar tag, gh release, ou invocar publish-release.
disable-model-invocation: true
---

# Publicar release (fusion-nfsu2)

Fluxo único: push → tag/release nova → apagar releases e tags antigas.

## Quando usar

Somente quando o usuário pedir explicitamente (ou invocar esta skill). Não publicar sozinho.

## Entradas obrigatórias

Pedir o que faltar:

| Entrada | Exemplo | Onde |
| --- | --- | --- |
| Versão | `1.5` | tag `v1.5`, pasta `local/release-v1.5/`, notes `release/notes-v1.5.md` |
| Título | `v1.5 — descrição curta` | `--title` da release |
| Notes | arquivo já existente | `release/notes-vX.Y.md` |

Padrão da pasta de artefatos: `local/release-vX.Y/` (não versionada).

## Artefatos obrigatórios

Antes de qualquer `gh`, confirmar que existem:

```
local/release-vX.Y/Fusion2018_AWD_NFSU2.zip
local/release-vX.Y/Fusion2012_FWD_NFSU2.zip
local/release-vX.Y/instalar.bat
local/release-vX.Y/globalb_patch.ps1
local/release-vX.Y/SHA256SUMS.txt
local/release-vX.Y/SHA256SUMS-conteudo.txt
release/notes-vX.Y.md
```

Se faltar algum, parar e informar. Não inventar ZIP nem notes.

## Checklist

```
Progresso:
- [ ] 1. Resolver gh
- [ ] 2. Validar artefatos e notes
- [ ] 3. Push da branch (commit só se o usuário pedir)
- [ ] 4. Criar release vX.Y com --latest
- [ ] 5. Apagar todas as releases/tags anteriores
- [ ] 6. Confirmar URL e lista final
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

1. `git status` e `git log -1 --oneline`.
2. Se houver alterações não commitadas: **não commitar** a menos que o usuário peça commit nesta mensagem. Avisar e aguardar.
3. Push da branch atual (em geral `main`):

```powershell
git push -u origin HEAD
```

Se o push falhar por auth/rede, parar — sem criar release desencontrada do remoto.

## Passo 3 — criar release e limpar antigas

Preferir o script da skill (PowerShell, na raiz do repo):

```powershell
.cursor/skills/publish-release/scripts/publish-release.ps1 `
  -Version 1.5 `
  -Title "v1.5 — descrição curta"
```

O script:

1. Valida os 6 artefatos + `release/notes-vX.Y.md`
2. Resolve `gh` (PATH ou `%TEMP%\gh-cli`)
3. Roda o equivalente a:

```powershell
gh release create vX.Y `
  local/release-vX.Y/Fusion2018_AWD_NFSU2.zip `
  local/release-vX.Y/Fusion2012_FWD_NFSU2.zip `
  local/release-vX.Y/instalar.bat `
  local/release-vX.Y/globalb_patch.ps1 `
  local/release-vX.Y/SHA256SUMS.txt `
  local/release-vX.Y/SHA256SUMS-conteudo.txt `
  --title "<título>" `
  --notes-file release/notes-vX.Y.md `
  --latest
```

4. Lista releases existentes e, para cada tag **diferente** da nova, executa:

```powershell
gh release delete <tag> --cleanup-tag -y
```

5. Imprime a URL da release e `gh release list`.

Flags úteis do script:

- `-SkipPush` — só release (push já feito)
- `-Push` — faz `git push -u origin HEAD` antes
- `-GhPath` — caminho explícito do `gh.exe`

## Regras

- Uma release pública por vez: a nova é `--latest`; as anteriores saem (tag + release).
- Não apagar a release que acabou de criar.
- Não usar `pint` / Laravel Sail (irrelevante neste repo).
- Responder em português com a URL final.
- Histórico git antigo permanece; só some a release/tag no GitHub.

## Exemplo (v1.4)

```powershell
.cursor/skills/publish-release/scripts/publish-release.ps1 `
  -Version 1.4 `
  -Title "v1.4 — luzes do 2012 e farol de milha do 2018" `
  -Push
```
