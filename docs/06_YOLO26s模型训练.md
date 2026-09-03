# 06 YOLO26s 模型训练

## 本章目标

理解本项目的四阶段复现路线，能够先做配置演练、启动训练、观察输出、处理显存不足并从 `last.pt` 断点续训。

## 1. 开始前检查

```powershell
conda activate car_damage_yolo26
python scripts/check_dataset.py
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU')"
```

数据必须 PASS。默认训练配置要求 `device: 0`，如果 CUDA 为 False 会主动停止，而不是悄悄使用 CPU 训练几天。

## 2. 为什么使用预训练权重

`yolo26s.pt` 是在大型通用数据上训练过的起点，它已经学到边缘、纹理和常见物体特征。本项目训练属于迁移学习：继续让已有模型适应车身缺陷。它不同于最终的 `best.pt`；首次运行如果本地没有 `yolo26s.pt`，Ultralytics 会联网下载官方权重。

从随机参数开始训练需要更多数据和时间，当前数据规模不推荐。

## 3. 永远先运行 dry-run

```powershell
python scripts/train.py --config configs/train.yaml --dry-run
```

dry-run 会检查数据、解析所有路径并打印最终参数，但不会下载模型或启动训练。确认 `data`、`model`、`project`、`name`、`device` 正确后再正式运行。

## 4. 完整复现实验的四个阶段

推荐两分类指标来自逐步实验，不是单条命令凭空得到。

### 阶段一：训练三分类基线

```powershell
python scripts/train.py --config configs/train.yaml
```

主要配置：150 epochs、640 输入、自动 batch、patience 30。输出：

```text
runs/car_damage/yolo26s_640/
├─ weights/best.pt
├─ weights/last.pt
├─ results.csv
├─ results.png
└─ confusion_matrix.png
```

### 阶段二：生成 crack 两倍平衡训练集

```powershell
python scripts/build_balanced_dataset.py `
  --data configs/data.yaml `
  --output .runtime/balanced_dataset_f2 `
  --class-id 1 `
  --factor 2
```

只平衡训练集，验证集仍指向原始 val。这里的目标是让模型多看到少数类，但不会复制验证样本虚增指标。

### 阶段三：以 768 输入微调三分类模型

```powershell
python scripts/train.py --config configs/train_finetune_768.yaml
```

它从 `runs/car_damage/yolo26s_640/weights/best.pt` 开始，使用较低学习率和温和增强，输出到 `runs/car_damage/yolo26s_finetune_768/`。

### 阶段四：生成两分类数据并训练最终模型

```powershell
python scripts/build_two_class_dataset.py
python scripts/train.py --config configs/train_two_class_768.yaml
```

最终输出：

```text
runs/car_damage/yolo26s_two_class_768/weights/best.pt
```

这条路线用于尽量接近仓库报告的 73.18% mAP50。由于 GPU、驱动、随机运算和库版本差异，重复训练的最后几位数字可能不同。

## 5. 笔记本推荐参数

RTX 4090 实验配置使用 batch 32，普通笔记本可能显存不足。可以覆盖为 10：

```powershell
python scripts/train.py --config configs/train_two_class_768.yaml --batch 10
```

仍然显存不足时依次尝试 8、4、2。想先确认流程能跑通：

```powershell
python scripts/train.py --config configs/train_two_class_768.yaml --epochs 1 --batch 10 --name smoke_test
```

一轮训练只能证明流程可运行，不能代表模型已经收敛。

## 6. 参数为什么这样设置

- `imgsz: 768`：保留较细的划痕信息；实验中提高到 960 反而降低指标并减慢推理。
- `workers: 0`：Windows 最稳定，避免多进程启动问题。
- `amp: true`：GPU 混合精度通常更快且节省显存。
- `AdamW`：用于后续微调，配合较低学习率减少破坏已有特征。
- `mosaic: 0.20`：保留一定组合增强，但避免细微缺陷被过度改变。
- `patience`：长期没有改善时早停，减少无效训练。
- `seed: 42`：提高复现实验的一致性，但不能消除所有 GPU 非确定性。

## 7. 断点续训

意外关机后，使用本次运行目录里的 `last.pt`：

```powershell
python scripts/train.py --resume runs/car_damage/yolo26s_two_class_768/weights/last.pt
```

resume 会恢复优化器和轮数状态。若只想拿旧权重开始一个全新的微调实验，应把它写到配置的 `model`，不要使用 `--resume`。

## 8. 常见问题

### `CUDA out of memory`

减小 batch；关闭其他占用显卡的软件；必要时降低 imgsz。不要只因为 OOM 就删除数据。

### 找不到上一阶段 best.pt

说明你跳过了前一阶段，或 Ultralytics 因同名目录已存在生成了 `yolo26s_6402` 等目录。查看训练结束输出中的 `save_dir`，再修正下一阶段配置路径。

### 为什么同名目录后面多了数字

配置 `exist_ok: false` 用于保护已有实验，Ultralytics 会创建新目录。记录每次实验的准确目录，不要仅凭猜测选择权重。

### loss 下降但 mAP 不提高

可能过拟合，也可能标签质量限制了上限。应检查验证指标和错误案例，而不是只看训练损失。

## 成功标准

训练正常结束或早停，并在对应运行目录找到非空的 `best.pt` 与 `last.pt`。下一步用 [07 模型验证与指标理解](07_模型验证与指标理解.md) 独立验证 best.pt。
