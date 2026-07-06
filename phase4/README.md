# Phase 4 ML Model Training

Phase 4 contains only the ML training and edge inference work for the Plant Disease Detection Rover prototype.

**Implementation status:** Completed.

It provides:

- dataset validation and manifest generation,
- TensorFlow/Keras transfer-learning training,
- evaluation reports,
- TensorFlow Lite export and validation,
- Raspberry Pi compatible TFLite inference,
- Phase 5 OpenCV severity-estimation integration for JSON compatibility.

## Completed Phase 4 Results

| Item | Final Result |
|---|---|
| Dataset source | PlantVillage |
| Model | MobileNetV3 transfer learning |
| Framework | TensorFlow 2.17.1 |
| Input size | 224 x 224 x 3 |
| Classes | `potato_healthy`, `potato_early_blight`, `potato_late_blight` |
| Final dataset size | 3,101 images |
| Test accuracy | 97.37% |
| Test loss | 0.057 |
| Deployment artifact | `model.tflite` |
| TFLite model size | 1,110,664 bytes, approximately 1.1 MB |
| TFLite input shape | `[1, 224, 224, 3]` |
| TFLite output shape | `[1, 3]` |
| Validated inference | `potato_late_blight`, confidence `0.999964`, approximately `11.943 ms` |

Detailed implementation documentation is in `phase4/docs/PHASE4_ML_TECHNICAL_DOCUMENTATION.md`.
Phase 5 severity documentation is in `docs/PHASE5_SEVERITY_ESTIMATION.md`.

## Dataset Summary

The final Phase 4 dataset uses PlantVillage potato classes. The original healthy class had only 152 images while late blight had 1001 images, creating significant class imbalance. Healthy potato images were augmented using horizontal flip, rotation from -15 degrees to +15 degrees, brightness adjustment, and contrast adjustment.

| Class | Images |
|---|---:|
| Potato Healthy | 1200 |
| Potato Early Blight | 1000 |
| Potato Late Blight | 1001 |
| Total | 3101 |

## Quick Commands

```powershell
python -m phase4.app.dataset --dataset-dir dataset --manifest phase4/runs/dataset_manifest.csv
python -m phase4.app.train --config phase4/configs/default.json --dataset-dir dataset --output-dir phase4/runs/mobilenetv3
python -m phase4.app.evaluate --model phase4/runs/mobilenetv3/saved_model.keras --dataset-dir dataset --split test
python -m phase4.app.export_tflite --model phase4/runs/mobilenetv3/saved_model.keras --output phase4/runs/mobilenetv3/model.tflite
python -m phase4.app.inference --model phase4/runs/mobilenetv3/model.tflite --labels phase4/runs/mobilenetv3/labels.json --image captures/sample.jpg --row-index 1 --plant-index 7
python -m phase4.app.validate_severity --image captures/sample.JPG --output-dir phase4/runs/severity_validation
```

Dataset files and trained binaries are not committed to this repository. The documented metrics above come from the completed Phase 4 PlantVillage training run and should be reproduced from the local dataset and exported artifacts during evaluation.
