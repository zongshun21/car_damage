# 10 GUI 安装、运行与跨设备迁移

本平台面向 Windows 10/11，采用“项目目录 + 独立 Conda 环境”的部署方式。不同电脑的用户名、盘符或显卡可以不同，代码没有绑定开发电脑的绝对路径。

## 1. 复制或下载工程

有 Git 时：

```powershell
git clone https://github.com/zongshun21/car_damage.git
cd car_damage
```

也可以在 GitHub 页面选择 **Code → Download ZIP**，解压后进入项目目录。权重在仓库中以分块保存，下面的安装脚本会自动还原成两份 `.pt` 并校验；GitHub 网页下载较慢时，不要在 ZIP 尚未完成时解压。

## 2. 安装 GUI 环境

安装过 Miniconda 后，在项目目录打开 PowerShell：

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_gui_env.ps1
```

脚本默认创建 `car_damage_gui` 环境，并安装经过验证的 Python、PyTorch、Ultralytics、PyQt6 和 Pillow。NVIDIA 显卡电脑使用默认命令；没有 NVIDIA 显卡时使用：

```powershell
.\setup_gui_env.ps1 -CpuOnly
```

如果希望沿用已有环境：

```powershell
.\setup_gui_env.ps1 -EnvName dl
```

## 3. 启动前检查

```powershell
.\check_gui_env.ps1 -EnvName car_damage_gui
```

检查脚本会先自动还原权重，再验证 Python 包、模型清单、两份内置权重以及基本导入。全部通过后启动：

```powershell
.\start_gui.ps1 -EnvName car_damage_gui
```

若使用 `dl` 环境，把命令中的环境名改成 `dl`。推荐使用启动脚本，因为它会处理 Qt 高 DPI 兼容设置、工作目录和错误日志。

## 4. 两个页面怎样使用

“首页概览”用于查看本机累计任务、图片和缺陷数量，也可清空这些统计。“智能检测”是主要工作页面：

1. 在模型下拉框选择两分类或三分类模型；
2. 选择 `auto`、`cpu` 或可用的 CUDA 设备；
3. 点击“打开图片”或“打开文件夹”；
4. 原图立即显示在图片预览窗口；
5. 点击“缺陷检测”，完成后同一窗口显示中文标注图；
6. 查看明细、速度、任务统计，必要时导出 CSV。

两分类模型精度更高，适合常规演示。三分类模型能够输出裂纹，但裂纹样本少，可靠性明显较低。

## 5. 参数建议

| 参数 | 推荐值 | 说明 |
|---|---:|---|
| 设备 | auto | 有兼容 GPU 时自动使用，否则使用 CPU |
| 置信度 | 0.25 | 越低越容易检出，也更可能误报 |
| IoU | 0.70 | 控制重叠检测框的合并 |
| 输入尺寸 | 768 | 与最终训练和验证保持一致 |

如果漏检较多，可将置信度降到 `0.15~0.20`；如果误检较多，可提高到 `0.35~0.50`。阈值调整只是改变显示取舍，并不会重新训练模型。

## 6. 导入自己的训练权重

训练结束后，权重一般在 `runs/detect/<实验名>/weights/best.pt`。在 GUI 中点击“导入模型”，选择该文件并填写便于识别的名称。程序会复制到 `models/custom/` 并登记到清单，之后可直接从下拉框选择。

只有来源可信的 `.pt` 文件才应导入。PyTorch 权重可能携带可执行的序列化内容，不要运行陌生网站下载的文件。

## 7. 迁移到另一台 Windows 电脑

需要复制的是仓库中的代码、配置和完整的 `models/`（包括 `weights_parts/`）。不需要复制原电脑的 Conda 环境、`.runtime/`、`runs/`、`__pycache__/` 或历史数据库。到新电脑后重新运行环境脚本，可避免 CUDA、Python 路径和用户目录不同造成的问题。

迁移检查清单：

- 64 位 Windows 10/11；
- Miniconda 可执行；
- 项目路径完整，权重文件大小正常；
- NVIDIA 用户已安装合适的显卡驱动；
- 执行 `check_gui_env.ps1` 无错误；
- 用一张图片完成端到端检测。

CPU 电脑也能运行，只是速度较慢。模型本身无需重新训练。

## 8. SSH 和远程桌面区别

普通 SSH 会话通常没有 Windows 图形桌面，所以进程可能启动但看不到窗口。这不是模型或 PyQt 代码故障。请在电脑本地登录桌面，或使用能够显示桌面的远程桌面软件运行 GUI。SSH 更适合执行训练、测试和命令行推理。

## 9. 可选：打包为发布目录

```powershell
.\scripts\package_gui.ps1
```

打包脚本会在 `release/` 生成便于复制的目录和 ZIP，并额外生成 SHA256 校验文件。仍建议在目标电脑运行配套环境安装脚本，而不是直接复制 Conda 环境。发布前检查目录中是否包含 `models.json` 和所需权重。若同名发布目标已经存在，脚本会停止以免覆盖旧包；可用 `-ReleaseName 新名称` 指定另一个名称。

下一章：[常见错误排查](11_常见错误排查.md)。
