param(
    [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root

if ([string]::IsNullOrWhiteSpace($Version)) {
    $Version = Get-Date -Format "yyyyMMdd-HHmmss"
}

function Get-PythonCommand {
    $Candidates = @()

    $VenvPython = Join-Path $Root ".venv\Scripts\python.exe"
    if (Test-Path $VenvPython) {
        $Candidates += $VenvPython
    }

    $Python = Get-Command python -ErrorAction SilentlyContinue
    if ($Python) {
        $Candidates += $Python.Source
    }

    $Py = Get-Command py -ErrorAction SilentlyContinue
    if ($Py) {
        $Candidates += $Py.Source
    }

    foreach ($Candidate in $Candidates) {
        $PreviousErrorActionPreference = $ErrorActionPreference
        $ErrorActionPreference = "Continue"
        & $Candidate -m pip --version *> $null
        $ExitCode = $LASTEXITCODE
        $ErrorActionPreference = $PreviousErrorActionPreference

        if ($ExitCode -eq 0) {
            return $Candidate
        }
    }

    throw "Python com pip nao encontrado. Instale Python 3 marcando a opcao 'Add Python to PATH'."
}

$PythonCommand = Get-PythonCommand

Write-Host "Usando Python: $PythonCommand"
Write-Host "Instalando dependencias..."
& $PythonCommand -m pip install -r requirements.txt
& $PythonCommand -m pip install pyinstaller

Write-Host "Gerando executavel..."
& $PythonCommand -m PyInstaller LifeOS.spec --clean --noconfirm

$BuiltExe = Join-Path $Root "dist\LifeOS\LifeOS.exe"
if (!(Test-Path $BuiltExe)) {
    throw "Build terminou, mas o executavel nao foi encontrado em $BuiltExe"
}

$MainExe = Join-Path $Root "LifeOS.exe"
$ArchiveDir = Join-Path $Root "executables"
$ArchiveExe = Join-Path $ArchiveDir "LifeOS-$Version.exe"

New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null
Copy-Item -Path $BuiltExe -Destination $MainExe -Force
Copy-Item -Path $BuiltExe -Destination $ArchiveExe -Force

Write-Host ""
Write-Host "Executavel principal criado:"
Write-Host $MainExe
Write-Host ""
Write-Host "Copia versionada criada:"
Write-Host $ArchiveExe
