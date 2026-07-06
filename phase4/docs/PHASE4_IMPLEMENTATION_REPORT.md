# Phase 4 Implementation Report

## Overview

Phase 4 of the Plant Disease Detection Rover has been completed. The implemented ML system trains a lightweight MobileNetV3 transfer-learning classifier using TensorFlow 2.17.1 and exports the trained model to TensorFlow Lite for Raspberry Pi edge inference.

The implementation is limited to Phase 4 responsibilities:

- dataset preparation,
- dataset validation,
- data augmentation,
- model training,
- model evaluation,
- TensorFlow Lite export,
- inference pipeline validation.

It does not implement rover movement, backend APIs, OpenRouter treatment generation, Telegram notification, or production severity segmentation.

## Dataset

Dataset source: PlantVillage.

Original dataset:

| Class | Images |
|---|---:|
| Healthy | 152 |
| Late Blight | 1001 |

Issue: the original dataset had significant class imbalance.

Solution: data augmentation was applied to healthy potato leaf images.

Augmentation techniques:

- Horizontal flip
- Rotation from -15 degrees to +15 degrees
- Brightness adjustment
- Contrast adjustment

Final dataset:

| Class | Images |
|---|---:|
| Potato Healthy | 1200 |
| Potato Early Blight | 1000 |
| Potato Late Blight | 1001 |
| Total | 3101 |

Final dataset structure:

```text
dataset/
├── train/
│   ├── potato_healthy/
│   ├── potato_early_blight/
│   └── potato_late_blight/
├── val/
│   ├── potato_healthy/
│   ├── potato_early_blight/
│   └── potato_late_blight/
└── test/
    ├── potato_healthy/
    ├── potato_early_blight/
    └── potato_late_blight/
```

## Training Configuration

| Parameter | Value |
|---|---|
| Model | MobileNetV3 transfer learning |
| Framework | TensorFlow 2.17.1 |
| Input size | 224 x 224 x 3 |
| Classes | 3 |
| Epochs | 20 |
| Classes trained | `potato_healthy`, `potato_early_blight`, `potato_late_blight` |

## Evaluation Results

| Model Run | Dataset Size | Classes | Test Accuracy | Test Loss |
|---|---:|---:|---:|---:|
| Initial model | 302 | 2 | 88.00% | Not recorded |
| Improved MobileNetV3 model | 3101 | 3 | 97.37% | 0.057 |

The improved model increased dataset size, added early blight classification, and improved test accuracy from 88.00% to 97.37%.

## TensorFlow Lite Deployment

TensorFlow Lite export completed successfully.

| Export Item | Result |
|---|---|
| Exported model | `model.tflite` |
| Input shape | `[1, 224, 224, 3]` |
| Output shape | `[1, 3]` |
| Model size | 1,110,664 bytes, approximately 1.1 MB |
| Deployment target | Raspberry Pi |
| Operation mode | Offline edge inference |

## Inference Validation

Validated inference output:

```json
{
  "class_name": "potato_late_blight",
  "crop": "potato",
  "disease": "late_blight",
  "confidence": 0.999964,
  "inference_time_ms": 11.943
}
```

The inference pipeline is functional. The validated prediction confidence exceeded 99.99%, and inference time was approximately 12 ms.

## Academic Evaluation Notes

The completed Phase 4 result demonstrates that a lightweight MobileNetV3 classifier can be trained on PlantVillage potato disease data and converted into a compact TensorFlow Lite model suitable for Raspberry Pi deployment. The model is small, supports offline inference, and produces structured predictions that can feed the rover's downstream treatment and notification workflow.

