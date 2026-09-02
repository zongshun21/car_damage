# YOLO26s 车辆车身缺陷检测

本项目使用 Ultralytics YOLO26s 训练三个车辆车身缺陷类别：

- `dent`：凹陷、钣金形变
- `crack`：真实开裂或断裂
- `scratch`：漆面划痕或擦伤

项目默认只支持单张图片和图片文件夹推理。原始数据集不会被脚本修改。

## 1. 目录要求

将数据集保留在项目根目录：

```text
car_damage/
├── 车损车身数据集/
│   ├── train/images/
│   ├── train/labels/
│   ├── val/images/
│   └── val/labels/
├── configs/
├── scripts/
└── ...
```

数据集不会提交到 GitHub，`.gitignore` 已将其排除。

## 2. 安装环境

在项目根目录打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_env.ps1
```

脚本会创建 Python 3.11 环境 `car_damage_yolo26`，安装 PyTorch 2.11 CUDA 12.8、Ultralytics 8.4.115 和测试依赖。它只在当前安装进程中忽略损坏的用户级 `pip.ini`，不会修改或删除全局配置。

CPU 环境可使用：

```powershell
.\setup_env.ps1 -CpuOnly
```

## 3. 检查数据集

```powershell
conda run -n car_damage_yolo26 python scripts/check_dataset.py
```

保存 JSON 报告：

```powershell
conda run -n car_damage_yolo26 python scripts/check_dataset.py --json runs/dataset_report.json
```

预期当前数据集检查结果为 `PASS`。六个空标签会报告为背景样本；三个宽度为0的框会报告为警告。二者都符合当前 Ultralytics 加载行为，不会阻止训练。

## 4. 先做训练配置演练

下面的命令检查数据并显示最终参数，不下载权重、不加载模型、不训练：

```powershell
conda run -n car_damage_yolo26 python scripts/train.py --dry-run
```

## 5. 启动正式训练

```powershell
conda run -n car_damage_yolo26 python scripts/train.py
```

默认参数：YOLO26s、640 输入、150 epochs、30 epochs 早停、自动 batch、GPU 0、AMP。首次运行会自动下载 `yolo26s.pt`。

常用覆盖：

```powershell
conda run -n car_damage_yolo26 python scripts/train.py --epochs 200 --batch 32 --name yolo26s_exp2
```

默认输出：

```text
runs/car_damage/yolo26s_640/
├── weights/best.pt
└── weights/last.pt
```

如果同名运行目录已存在，Ultralytics 会创建递增目录，终端输出中的 `save_dir` 才是本次准确位置。

## 6. 断点续训

```powershell
conda run -n car_damage_yolo26 python scripts/train.py --resume runs/car_damage/yolo26s_640/weights/last.pt
```

断点不存在时脚本会直接报错，不会意外开启新训练。

## 7. 验证最佳权重

```powershell
conda run -n car_damage_yolo26 python scripts/validate.py `
  --weights runs/car_damage/yolo26s_640/weights/best.pt
```

脚本输出 Precision、Recall、mAP50、mAP50-95 和每类别 mAP，并让 Ultralytics 保存混淆矩阵与验证图。

## 8. 图片推理

单张图片：

```powershell
conda run -n car_damage_yolo26 python scripts/predict.py `
  --weights runs/car_damage/yolo26s_640/weights/best.pt `
  --source path/to/car.jpg
```

整个图片目录：

```powershell
conda run -n car_damage_yolo26 python scripts/predict.py `
  --weights runs/car_damage/yolo26s_640/weights/best.pt `
  --source path/to/images `
  --conf 0.25 `
  --save-txt `
  --save-conf
```

默认输出目录为 `runs/car_damage/predict/`。

CPU 推理：

```powershell
conda run -n car_damage_yolo26 python scripts/predict.py `
  --weights runs/car_damage/yolo26s_640/weights/best.pt `
  --source path/to/car.jpg `
  --device cpu
```

## 9. 运行项目测试

```powershell
conda run -n car_damage_yolo26 python -m pytest
```

测试会完整读取当前 5,700 张图片，但不会启动训练。

## 常见问题

### CUDA 不可用

运行：

```powershell
conda run -n car_damage_yolo26 python -c "import torch; print(torch.__version__, torch.cuda.is_available())"
```

如果输出 `False`，确认 NVIDIA 驱动正常，并重新运行 `setup_env.ps1`。不要在系统 Python 3.14 环境中直接训练。

### 显存不足

自动 batch 通常会使用约 60% GPU 显存。仍然报错时指定更小 batch：

```powershell
conda run -n car_damage_yolo26 python scripts/train.py --batch 16
```

### Windows 多进程加载错误

默认 `workers=4`。如果系统环境不稳定，将 `configs/train.yaml` 中的 `workers` 改为 `0`。

### 下载权重失败

`yolo26s.pt` 首次运行需要网络。检查代理、防火墙和 GitHub 访问，再重新运行训练命令。

## 许可

Ultralytics 软件和训练模型默认受 AGPL-3.0 约束。个人学习、研究和完整开源项目通常适用；闭源或商业部署前请查看 Ultralytics 官方许可并评估是否需要 Enterprise License。

