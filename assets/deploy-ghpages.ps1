<#
  deploy-ghpages.ps1 (archivio in assets/)

  Copia del vecchio script di deploy locale. Il deploy ufficiale è gestito dal
  workflow GitHub Actions in `.github/workflows/deploy-site.yml`.

  Questo file rimane a scopo di riferimento e per esecuzione manuale locale se
  necessario. Non è necessario per il deployment automatico.

  Uso (locale, Windows PowerShell):
    powershell -ExecutionPolicy Bypass -File .\assets\deploy-ghpages.ps1

  Attenzione: lo script forza il push su `gh-pages` (git push -f). Usalo con
  cautela.
#>

Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition
$publish = Join-Path $root '..\publish'

Write-Host "Preparing publish folder at: $publish"

if (Test-Path $publish) {
    Remove-Item -Recurse -Force $publish
}

New-Item -ItemType Directory -Path $publish | Out-Null

Write-Host "Copying SITO content..."
Copy-Item -Path (Join-Path $root '..\SITO\*') -Destination $publish -Recurse -Force -ErrorAction SilentlyContinue

foreach ($f in @('CANDIDATURA','DIARIO DI BORDO','GLOSSARIO','assets')) {
    $src = Join-Path $root "..\$f"
    if (Test-Path $src) {
        Write-Host "Copying $f..."
        Copy-Item -Path $src -Destination (Join-Path $publish $f) -Recurse -Force
    }
}

# Create .nojekyll to prevent GitHub Pages from processing the site with Jekyll
$nojekyll = Join-Path $publish '.nojekyll'
New-Item -Path $nojekyll -ItemType File -Force | Out-Null

$origin = git -C $root config --get remote.origin.url 2>$null
if (-not $origin) {
    Write-Error "No git remote origin found. Configure remote.origin first (git remote add origin <url>)."
    exit 1
}

Write-Host "Initializing temporary git repo inside publish/ and pushing to gh-pages branch..."

Push-Location $publish
try {
    git init | Out-Null
    git add --all
    git commit -m "Deploy site: $(Get-Date -Format o)" --author "deploy-script <deploy@local>" | Out-Null
    git branch -M gh-pages
    git remote add origin $origin
    git push -f origin gh-pages
} catch {
    Write-Error "Deploy failed: $_"
    exit 1
} finally {
    Pop-Location
}

Write-Host "Deploy finished. The gh-pages branch has been updated."
