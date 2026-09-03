# GUI 使用与部署说明

本项目提供“首页概览”和“智能检测”两个页面。平台可选择内置或用户导入的 YOLO26s 权重，支持单图/文件夹检测、中文缺陷标签、结果图片保存、CSV 导出、速度显示和本地历史统计。

## 快速启动

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\setup_gui_env.ps1
.\check_gui_env.ps1
.\start_gui.ps1
```

没有 NVIDIA 显卡时，安装第一步改为：

```powershell
.\setup_gui_env.ps1 -CpuOnly
```

已有 `dl` 环境时，可在检查和启动命令后加 `-EnvName dl`。

## 使用顺序

1. 进入“智能检测”，选择模型和设备；
2. 打开图片或文件夹，预览窗口先显示原图；
3. 点击“缺陷检测”，同一窗口显示中文标注结果；
4. 查看检测明细、FPS 和统计，可导出 CSV 或打开输出目录；
5. 首页统计可按需清空，清空不会删除权重。

默认输出目录为当前用户的“文档/CarDamageResults”。设置、历史数据库和启动日志位于 `%LOCALAPPDATA%\LZPU\CarDamagePlatform`，所有检测均在本机完成。

## 迁移说明

复制完整项目到另一台 Windows 电脑后重新运行环境安装脚本，不要复制原电脑的 Conda 环境。仓库中的 `models/weights_parts/` 会由脚本自动还原并校验为两份 `.pt`。普通 SSH 会话没有可见图形桌面，请在本机桌面或远程桌面会话运行 GUI。

详细原理见 [GUI 平台原理与封装](docs/09_GUI平台原理与封装.md)，完整安装、参数和迁移步骤见 [GUI 安装运行与迁移](docs/10_GUI安装运行与迁移.md)，异常处理见 [常见错误排查](docs/11_常见错误排查.md)。
