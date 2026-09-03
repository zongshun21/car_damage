param(
    [Parameter(Mandatory = $true)]
    [string]$Source,
    [string]$Weights = "models/YOLO26s_DentScratch_mAP50_73.18.pt",
    [string]$Device = "0",
    [string]$Output = "runs/car_damage/predict_two_class",
    [double]$Confidence = 0.25,
    [int]$ImageSize = 768
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $projectRoot "restore_models.ps1")
$weightsPath = if ([System.IO.Path]::IsPathRooted($Weights)) {
    $Weights
} else {
    Join-Path $projectRoot $Weights
}
$predictScript = Join-Path $projectRoot "scripts/predict.py"

if (-not (Test-Path -LiteralPath $weightsPath -PathType Leaf)) {
    throw "Best weights not found: $weightsPath"
}

$python = if ($env:CONDA_PREFIX) {
    Join-Path $env:CONDA_PREFIX "python.exe"
} else {
    (Get-Command python -ErrorAction Stop).Source
}

& $python $predictScript `
    --weights $weightsPath `
    --source $Source `
    --device $Device `
    --conf $Confidence `
    --iou 0.70 `
    --imgsz $ImageSize `
    --output $Output `
    --save-txt `
    --save-conf

exit $LASTEXITCODE
