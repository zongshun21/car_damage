param(
    [string]$EnvName = "car_damage_gui"
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

& (Join-Path $projectRoot "restore_models.ps1")

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda was not found. Install Miniconda or Anaconda first."
}

Push-Location $projectRoot
try {
    conda run --no-capture-output -n $EnvName python scripts\gui.py
    if ($LASTEXITCODE -ne 0) {
        throw "The GUI exited with code $LASTEXITCODE. Run .\check_gui_env.ps1 first."
    }
} finally {
    Pop-Location
}
