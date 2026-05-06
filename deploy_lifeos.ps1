param(
    [string]$Message = "atualizacao life os"
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

git status --short
git add .

$Pending = git diff --cached --name-only
if ([string]::IsNullOrWhiteSpace($Pending)) {
    Write-Host "Nenhuma alteracao para publicar."
    exit 0
}

git commit -m $Message
git push

Write-Host ""
Write-Host "Atualizacao enviada. O Render deve iniciar o rebuild automaticamente."
