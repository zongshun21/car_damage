param(
    [string]$EnvName = "car_damage_gui",
    [switch]$CpuOnly
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

& (Join-Path $projectRoot "restore_models.ps1")

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda was not found. Install Miniconda or Anaconda first."
}

$previousPipConfig = $env:PIP_CONFIG_FILE
try {
    $env:PIP_CONFIG_FILE = "NUL"
    $environmentPaths = (conda env list --json | ConvertFrom-Json).envs
    $exists = $environmentPaths | Where-Object { (Split-Path -Leaf $_) -eq $EnvName }
    if (-not $exists) {
        conda create -n $EnvName python=3.11 pip -y
        if ($LASTEXITCODE -ne 0) { throw "Failed to create Conda environment." }
    }

    conda run -n $EnvName python -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw "Failed to update pip tooling." }

    $torchIndex = if ($CpuOnly) {
        "https://download.pytorch.org/whl/cpu"
    } else {
        "https://download.pytorch.org/whl/cu124"
    }
    conda run -n $EnvName python -m pip install torch==2.5.1 torchvision==0.20.1 --index-url $torchIndex
    if ($LASTEXITCODE -ne 0) { throw "Failed to install PyTorch." }

    conda run -n $EnvName python -m pip install -e "$projectRoot"
    if ($LASTEXITCODE -ne 0) { throw "Failed to install project dependencies." }

    Write-Host "Environment ready: $EnvName" -ForegroundColor Green
    Write-Host "Check: .\check_gui_env.ps1 -EnvName $EnvName"
    Write-Host "Start: .\start_gui.ps1 -EnvName $EnvName"
} finally {
    if ($null -eq $previousPipConfig) {
        Remove-Item Env:PIP_CONFIG_FILE -ErrorAction SilentlyContinue
    } else {
        $env:PIP_CONFIG_FILE = $previousPipConfig
    }
}
