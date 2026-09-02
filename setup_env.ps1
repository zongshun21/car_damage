param(
    [string]$EnvName = "car_damage_yolo26",
    [switch]$CpuOnly
)

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

if (-not (Get-Command conda -ErrorAction SilentlyContinue)) {
    throw "未找到 conda。请先安装 Miniconda/Anaconda，并重新打开 PowerShell。"
}

$PreviousPipConfig = $env:PIP_CONFIG_FILE
try {
    # The user-level pip.ini contains a BOM that breaks pip parsing. Disable it only for this process.
    $env:PIP_CONFIG_FILE = "NUL"

    $Environments = conda env list --json | ConvertFrom-Json
    $Exists = $false
    foreach ($EnvironmentPath in $Environments.envs) {
        if ((Split-Path -Leaf $EnvironmentPath) -eq $EnvName) {
            $Exists = $true
            break
        }
    }

    if (-not $Exists) {
        Write-Host "创建 Conda 环境: $EnvName"
        conda create -n $EnvName python=3.11 pip -y
        if ($LASTEXITCODE -ne 0) { throw "Conda 环境创建失败" }
    }
    else {
        Write-Host "Conda 环境已存在: $EnvName"
    }

    conda run -n $EnvName python -m pip install --upgrade pip setuptools wheel
    if ($LASTEXITCODE -ne 0) { throw "基础安装工具升级失败" }

    $TorchIndex = if ($CpuOnly) {
        "https://download.pytorch.org/whl/cpu"
    }
    else {
        "https://download.pytorch.org/whl/cu128"
    }
    Write-Host "安装 PyTorch: $TorchIndex"
    conda run -n $EnvName python -m pip install torch==2.11.0 torchvision==0.26.0 --index-url $TorchIndex
    if ($LASTEXITCODE -ne 0) { throw "PyTorch 安装失败" }

    conda run -n $EnvName python -m pip install -e "$ProjectRoot[dev]"
    if ($LASTEXITCODE -ne 0) { throw "项目依赖安装失败" }

    conda run -n $EnvName python -c "import torch, ultralytics; print('torch=', torch.__version__); print('ultralytics=', ultralytics.__version__); print('cuda=', torch.cuda.is_available()); print('gpu=', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
    if ($LASTEXITCODE -ne 0) { throw "环境验证失败" }

    Write-Host "环境安装完成。运行数据检查："
    Write-Host "conda run -n $EnvName python scripts/check_dataset.py"
}
finally {
    if ($null -eq $PreviousPipConfig) {
        Remove-Item Env:PIP_CONFIG_FILE -ErrorAction SilentlyContinue
    }
    else {
        $env:PIP_CONFIG_FILE = $PreviousPipConfig
    }
}


