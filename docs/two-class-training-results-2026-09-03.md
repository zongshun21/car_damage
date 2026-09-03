# YOLO26s 两分类车辆缺陷训练结果

## 最终任务

模型检测以下两个类别：

- `0: dent`
- `1: scratch`

原数据中的 `crack` 标注已从派生数据集删除。原始数据集没有被修改；原 `scratch=2` 已在派生数据中映射为 `scratch=1`。

## 独立验证结果

验证集保持原划分，共 1,140 张图片、1,837 个目标，没有复制验证样本。

| 类别 | Precision | Recall | mAP50 | mAP50-95 |
|---|---:|---:|---:|---:|
| 全部 | 89.15% | 68.66% | **73.18%** | 56.68% |
| dent | 81.6% | 52.1% | 56.9% | 39.1% |
| scratch | 96.7% | 85.3% | 89.4% | 74.3% |

目标 mAP50 65% 已达到，实际高出约 8.18 个百分点。

## 文件

- 权重：`runs/car_damage/yolo26s_two_class_768/weights/best.pt`
- 训练配置：`configs/train_two_class_768.yaml`
- 数据配置：`configs/data_two_class.yaml`
- 独立验证输出：`runs/car_damage/two_class_final_validation`
- 数据检查报告：`runs/two_class_dataset_report.json`

## 推理

```powershell
conda activate dl
cd <你的项目目录>\car_damage
.\run_inference.ps1 -Source "图片路径或图片目录"
```

默认参数为 `imgsz=768`、`conf=0.25`。提高 `Confidence` 会减少误报但也可能漏检，例如：

```powershell
.\run_inference.ps1 -Source "图片目录" -Confidence 0.35
```
