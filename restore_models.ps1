param()

$ErrorActionPreference = "Stop"
$projectRoot = $PSScriptRoot
$modelsDir = Join-Path $projectRoot "models"
$partsDir = Join-Path $modelsDir "weights_parts"

$models = @(
    @{ Name = "YOLO26s_DentScratch_mAP50_73.18.pt"; Sha256 = "d6ff9016c22e5de5117854d4c5fe8b0a37f041031187a3146c8f75087a22d07a"; Size = 20332094 },
    @{ Name = "YOLO26s_DentCrackScratch_mAP50_53.10.pt"; Sha256 = "ba666ddbfd4a9f9da16e0bef2264797a1c0c02e8eec2f48d041753d042a553d2"; Size = 80393592 }
)

foreach ($model in $models) {
    $target = Join-Path $modelsDir $model.Name
    if (Test-Path -LiteralPath $target -PathType Leaf) {
        $existingHash = (Get-FileHash -LiteralPath $target -Algorithm SHA256).Hash.ToLowerInvariant()
        if ($existingHash -ne $model.Sha256) { throw "Existing model has an unexpected SHA256: $target" }
        Write-Host "Model ready: $($model.Name)"
        continue
    }

    if (-not (Test-Path -LiteralPath $partsDir -PathType Container)) { throw "Model parts directory is missing: $partsDir" }
    $parts = @(Get-ChildItem -LiteralPath $partsDir -File -Filter "$($model.Name).part*" | Sort-Object Name)
    if ($parts.Count -eq 0) { throw "No published parts found for $($model.Name)" }

    $temporary = "$target.assembling"
    if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force }
    $output = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write)
    try {
        foreach ($part in $parts) {
            $input = [IO.File]::OpenRead($part.FullName)
            try { $input.CopyTo($output) } finally { $input.Dispose() }
        }
    } finally {
        $output.Dispose()
    }

    $assembled = Get-Item -LiteralPath $temporary
    $assembledHash = (Get-FileHash -LiteralPath $temporary -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($assembled.Length -ne $model.Size -or $assembledHash -ne $model.Sha256) {
        Remove-Item -LiteralPath $temporary -Force
        throw "Model reconstruction failed integrity verification: $($model.Name)"
    }
    Move-Item -LiteralPath $temporary -Destination $target
    Write-Host "Restored and verified: $($model.Name)"
}

Write-Host "All built-in models are ready." -ForegroundColor Green
