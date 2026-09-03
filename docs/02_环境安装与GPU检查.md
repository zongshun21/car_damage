# 02 环境安装与 GPU 检查

## 本章目标

在 Windows 上创建一个与系统 Python 隔离的 Conda 环境，安装经过本项目验证的 PyTorch、Ultralytics、Pillow、PyQt6 和测试工具，并确认电脑实际使用的是 GPU 还是 CPU。

## 1. 为什么要单独创建环境

不同项目可能要求不同 Python 和依赖版本。直接把包全部装进系统 Python，容易出现“这个项目升级后另一个项目不能运行”。Conda 环境相当于项目专用工具箱，删除环境不会删除代码和数据。

本项目固定 Python 3.11。训练环境默认名为 `car_damage_yolo26`，GUI 环境默认名为 `car_damage_gui`。

## 2. 前置条件

1. Windows 10 或 Windows 11。
2. 至少预留 10 GB 磁盘空间；训练结果和数据会继续占用空间。
3. 安装 [Miniconda](https://docs.conda.io/projects/miniconda/en/latest/) 或 Anaconda。
4. 如果使用 NVIDIA GPU，先安装能正常工作的显卡驱动。
5. 重新打开 PowerShell，执行 `conda --version` 应能看到版本号。

不要求单独安装完整 CUDA Toolkit。PyTorch 的 CUDA wheel 自带运行时组件，但仍需要兼容的 NVIDIA 驱动。官方安装选择器见 [PyTorch Start Locally](https://pytorch.org/get-started/locally/)。

## 3. 获取代码

```powershell
git clone https://github.com/zongshun21/car_damage.git
cd car_damage
```

如果你是从 ZIP 下载，先完整解压，再在解压后的项目根目录打开 PowerShell。后续命令都默认当前目录是项目根目录。

## 4. 安装训练环境

PowerShell 默认可能禁止脚本，只对当前窗口临时放行：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
```

有 NVIDIA GPU：

```powershell
.\setup_env.ps1
```

只有 CPU：

```powershell
.\setup_env.ps1 -CpuOnly
```

脚本会依次完成：

1. 检查 Conda 是否存在。
2. 创建 Python 3.11 环境。
3. 安装 PyTorch 2.5.1 与 torchvision 0.20.1。
4. GPU 路线使用官方 CUDA 12.4 wheel；CPU 路线使用 CPU wheel。
5. 以可编辑模式安装本项目和 Ultralytics 8.4.115。
6. 打印 PyTorch、Ultralytics、CUDA 和显卡名称。

修改环境名：

```powershell
.\setup_env.ps1 -EnvName dl
```

后续就使用 `conda activate dl`，不要再激活默认名称。

## 5. 验证环境

```powershell
conda activate car_damage_yolo26
python -c "import torch, ultralytics; print(torch.__version__); print(ultralytics.__version__); print(torch.cuda.is_available()); print(torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

GPU 环境正常时，第三行应为 `True`，第四行是显卡名称。CPU 环境显示 `False` 和 `CPU` 是正常现象。

本项目实际验证环境：

```text
Python       3.11
torch        2.5.1
torchvision  0.20.1
CUDA build   12.4
ultralytics  8.4.115
Pillow       11.1.0
PyQt6        6.11.0
```

## 6. 只安装 GUI 环境

只想使用内置权重检测图片，可以运行：

```powershell
.\setup_gui_env.ps1
.\check_gui_env.ps1
```

CPU 设备：

```powershell
.\setup_gui_env.ps1 -CpuOnly
```

训练环境本身也包含 GUI 依赖。如果已经安装训练环境，可直接指定：

```powershell
.\check_gui_env.ps1 -EnvName car_damage_yolo26
.\start_gui.ps1 -EnvName car_damage_yolo26
```

## 7. 常见问题

### `conda` 不是命令

说明 Miniconda 未安装或终端没有刷新。安装后关闭并重新打开 PowerShell，或者从“Anaconda Prompt”运行。

### PyTorch 安装很慢

GPU wheel 较大，需要联网下载。不要关闭窗口。网络中断后重新运行安装脚本即可，脚本会复用已有环境。

### CUDA 为 False

先执行 `nvidia-smi`。如果命令不存在或报错，先修复 NVIDIA 驱动。如果只有集成显卡或 AMD 显卡，请使用 `-CpuOnly`。

### 出现显存不足

环境没有坏。训练时减小 batch，例如 `--batch 4`，或改用 `--device cpu`（会很慢）。

## 成功标准

`import torch, ultralytics, PyQt6` 均不报错，且你知道当前设备是 GPU 还是 CPU。下一步阅读 [03 数据集目录与 YOLO 标签格式](03_数据集目录与YOLO标签格式.md)。
