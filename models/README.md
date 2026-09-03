# 模型权重说明

本目录保存模型清单，以及两份可直接用于命令行推理或 PyQt6 GUI 的权重。GitHub 仓库中的原始字节位于 `weights_parts/`，运行根目录的 `restore_models.ps1` 后会逐字节还原出下列 `.pt`。安装、检查、启动和命令行推理脚本都会自动调用还原程序。

## 内置模型

| 文件 | 类别顺序 | 用途 | 大小 | mAP50 |
|---|---|---|---:|---:|
| `YOLO26s_DentScratch_mAP50_73.18.pt` | `dent, scratch` | 默认推荐的两分类检测 | 19.39 MB | 73.18% |
| `YOLO26s_DentCrackScratch_mAP50_53.10.pt` | `dent, crack, scratch` | 保留裂纹的三分类对照实验 | 76.67 MB | 53.10% |

三分类权重能够输出裂纹，但裂纹验证表现较弱，不建议把它当成高可靠裂纹检测器。文件名中的指标只用于区分物理权重；GUI 的模型显示名称不会携带精度。

## SHA256 完整性校验

下载仓库后先还原（通常安装脚本已自动完成）：

```powershell
.\restore_models.ps1
```

然后运行：

```powershell
Get-FileHash .\models\YOLO26s_DentScratch_mAP50_73.18.pt -Algorithm SHA256
Get-FileHash .\models\YOLO26s_DentCrackScratch_mAP50_53.10.pt -Algorithm SHA256
```

正确结果：

```text
d6ff9016c22e5de5117854d4c5fe8b0a37f041031187a3146c8f75087a22d07a  YOLO26s_DentScratch_mAP50_73.18.pt
ba666ddbfd4a9f9da16e0bef2264797a1c0c02e8eec2f48d041753d042a553d2  YOLO26s_DentCrackScratch_mAP50_53.10.pt
```

哈希不同通常意味着下载未完成、文件被改动或拿错版本，此时不要继续用该文件比较实验。

## `models.json` 的作用

GUI 启动时读取 `models.json`，根据其中的 `filename` 找到权重，并用 `display_name` 填充模型下拉框。路径均相对本目录，所以更换电脑、Windows 用户名或盘符后仍然有效。

类别顺序必须和模型训练时完全一致。两分类数据把原始 `scratch=2` 重映射为 `scratch=1`；不能把三分类清单直接套到两分类权重上。

## 使用自己的权重

最简单的方法是在 GUI 点击“导入模型”，程序会复制权重到 `models/custom/` 并更新清单。训练权重通常位于：

```text
runs/detect/<实验名称>/weights/best.pt
```

也可用命令行直接指定：

```powershell
python scripts/predict.py --weights path\to\best.pt --source path\to\image.jpg --device auto --imgsz 768
```

只加载可信来源的 PyTorch `.pt` 文件。模型文件属于可执行反序列化输入，不应运行陌生来源的权重。

更多内容见 [GUI 平台原理与封装](../docs/09_GUI平台原理与封装.md) 和 [实验结果与改进建议](../docs/12_实验结果与改进建议.md)。
