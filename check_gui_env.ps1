param(
    [string]$EnvName = "car_damage_gui"
)

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot

& (Join-Path $projectRoot "restore_models.ps1")

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "Conda was not found."
}

Push-Location $projectRoot
try {
    conda run -n $EnvName python -c "import PyQt6, torch, ultralytics; print('PyQt6=OK'); print('torch=' + torch.__version__); print('ultralytics=' + ultralytics.__version__); print('cuda=' + str(torch.cuda.is_available())); print('device=' + (torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'))"
    if ($LASTEXITCODE -ne 0) { throw "Python environment check failed." }

    $requiredModels = @(
        "models\YOLO26s_DentScratch_mAP50_73.18.pt",
        "models\YOLO26s_DentCrackScratch_mAP50_53.10.pt"
    )
    foreach ($model in $requiredModels) {
        $path = Join-Path $projectRoot $model
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
            throw "Required model is missing: $model"
        }
        Write-Host "Model OK: $model"
    }

    $env:QT_QPA_PLATFORM = "offscreen"
    conda run -n $EnvName python scripts\gui.py --smoke-test
    if ($LASTEXITCODE -ne 0) { throw "GUI smoke test failed." }
    Write-Host "GUI environment check passed." -ForegroundColor Green
} finally {
    Remove-Item Env:QT_QPA_PLATFORM -ErrorAction SilentlyContinue
    Pop-Location
}
