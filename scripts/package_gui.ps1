param(
    [string]$ReleaseName = "CarDamagePlatform_Windows_20260903",
    [string]$OutputDirectory = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$releaseRoot = if ($OutputDirectory) {
    [System.IO.Path]::GetFullPath($OutputDirectory)
} else {
    Join-Path $projectRoot "release"
}
$stageRoot = Join-Path $releaseRoot $ReleaseName
$zipPath = Join-Path $releaseRoot "$ReleaseName.zip"
$hashPath = "$zipPath.sha256"

foreach ($target in @($stageRoot, $zipPath, $hashPath)) {
    if (Test-Path -LiteralPath $target) {
        throw "Release target already exists: $target"
    }
}

New-Item -ItemType Directory -Path $releaseRoot -Force | Out-Null
New-Item -ItemType Directory -Path $stageRoot -Force | Out-Null

$rootFiles = @(
    "pyproject.toml",
    "README.md",
    "environment.yml",
    "setup_gui_env.ps1",
    "check_gui_env.ps1",
    "start_gui.ps1"
)

foreach ($relative in $rootFiles) {
    $source = Join-Path $projectRoot $relative
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required release file is missing: $relative"
    }
    Copy-Item -LiteralPath $source -Destination (Join-Path $stageRoot $relative)
}

$guiGuide = Get-ChildItem -LiteralPath $projectRoot -File -Filter "GUI*.md" | Select-Object -First 1
if ($null -eq $guiGuide) {
    throw "GUI deployment guide is missing."
}
Copy-Item -LiteralPath $guiGuide.FullName -Destination (Join-Path $stageRoot "GUI_DEPLOYMENT_CN.md")

$guiEntryDirectory = Join-Path $stageRoot "scripts"
New-Item -ItemType Directory -Path $guiEntryDirectory -Force | Out-Null
Copy-Item -LiteralPath (Join-Path $projectRoot "scripts\gui.py") -Destination $guiEntryDirectory

$sourceRoot = Join-Path $projectRoot "src"
Get-ChildItem -LiteralPath $sourceRoot -File -Recurse | Where-Object {
    $_.Extension -notin @(".pyc", ".pyo") -and $_.FullName -notmatch "__pycache__"
} | ForEach-Object {
    $relative = $_.FullName.Substring($sourceRoot.Length).TrimStart("\")
    $destination = Join-Path (Join-Path $stageRoot "src") $relative
    New-Item -ItemType Directory -Path (Split-Path -Parent $destination) -Force | Out-Null
    Copy-Item -LiteralPath $_.FullName -Destination $destination
}

$modelsRoot = Join-Path $projectRoot "models"
$requiredModels = @(
    "models.json",
    "README.md",
    "YOLO26s_DentScratch_mAP50_73.18.pt",
    "YOLO26s_DentCrackScratch_mAP50_53.10.pt"
)
New-Item -ItemType Directory -Path (Join-Path $stageRoot "models") -Force | Out-Null
foreach ($name in $requiredModels) {
    $source = Join-Path $modelsRoot $name
    if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
        throw "Required model asset is missing: $name"
    }
    Copy-Item -LiteralPath $source -Destination (Join-Path (Join-Path $stageRoot "models") $name)
}

$manifestPath = Join-Path $stageRoot "DEPLOYMENT_MANIFEST.txt"
$manifestLines = Get-ChildItem -LiteralPath $stageRoot -File -Recurse | Sort-Object FullName | ForEach-Object {
    $relative = $_.FullName.Substring($stageRoot.Length).TrimStart("\")
    $hash = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $relative"
}
[System.IO.File]::WriteAllLines($manifestPath, $manifestLines, [System.Text.UTF8Encoding]::new($false))

Compress-Archive -LiteralPath $stageRoot -DestinationPath $zipPath -CompressionLevel Optimal
$zipHash = (Get-FileHash -LiteralPath $zipPath -Algorithm SHA256).Hash.ToLowerInvariant()
[System.IO.File]::WriteAllText($hashPath, "$zipHash  $ReleaseName.zip`r`n", [System.Text.UTF8Encoding]::new($false))

$sizeMb = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1MB, 2)
Write-Host "Release directory: $stageRoot"
Write-Host "ZIP: $zipPath"
Write-Host "Size: $sizeMb MB"
Write-Host "SHA256: $zipHash"
