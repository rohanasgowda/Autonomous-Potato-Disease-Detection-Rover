from pathlib import Path
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

from sklearn.preprocessing import label_binarize
from sklearn.metrics import (
    roc_curve,
    auc,
    precision_recall_curve,
    average_precision_score,
)

# ==========================
# Paths
# ==========================

MODEL_PATH = "runs/mobilenetv3_augmented/checkpoints/best.keras"
DATASET_PATH = "../dataset/test"

IMG_SIZE = (224, 224)
BATCH_SIZE = 32

# ==========================
# Load Dataset
# ==========================

dataset = tf.keras.utils.image_dataset_from_directory(
    DATASET_PATH,
    image_size=IMG_SIZE,
    batch_size=BATCH_SIZE,
    shuffle=False,
)

class_names = dataset.class_names

print("Classes:", class_names)

# ==========================
# Load Model
# ==========================

model = tf.keras.models.load_model(MODEL_PATH)

# ==========================
# Prediction
# ==========================

y_true = []
y_score = []

for images, labels in dataset:

    predictions = model.predict(images, verbose=0)

    y_true.extend(labels.numpy())
    y_score.extend(predictions)

y_true = np.array(y_true)
y_score = np.array(y_score)

# One-hot labels

y_true_bin = label_binarize(
    y_true,
    classes=np.arange(len(class_names))
)

# ==========================
# ROC Curve
# ==========================

plt.figure(figsize=(8,6))

for i, name in enumerate(class_names):

    fpr, tpr, _ = roc_curve(
        y_true_bin[:, i],
        y_score[:, i]
    )

    roc_auc = auc(fpr, tpr)

    plt.plot(
        fpr,
        tpr,
        linewidth=3,
        label=f"{name} (AUC = {roc_auc:.3f})"
    )

plt.plot([0,1],[0,1],'k--',linewidth=1)

plt.grid(True, linestyle="--", alpha=0.4)

plt.xlim([0,1])

plt.ylim([0,1.05])

plt.xlabel("False Positive Rate", fontsize=12)

plt.ylabel("True Positive Rate", fontsize=12)

plt.title("ROC Curve", fontsize=14)

plt.legend(loc="lower right")

plt.tight_layout()

plt.savefig(
    "runs/mobilenetv3_augmented/roc_curve.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================
# Precision Recall Curve
# ==========================

plt.figure(figsize=(8,6))

for i, name in enumerate(class_names):

    precision, recall, _ = precision_recall_curve(
        y_true_bin[:, i],
        y_score[:, i]
    )

    ap = average_precision_score(
        y_true_bin[:, i],
        y_score[:, i]
    )

    plt.plot(
        recall,
        precision,
        linewidth=3,
        label=f"{name} (AP = {ap:.3f})"
    )

plt.grid(True, linestyle="--", alpha=0.4)

plt.xlim([0,1])

plt.ylim([0,1.05])

plt.xlabel("Recall", fontsize=12)

plt.ylabel("Precision", fontsize=12)

plt.title("Precision–Recall Curve", fontsize=14)

plt.legend(loc="lower left")

plt.tight_layout()

plt.savefig(
    "runs/mobilenetv3_augmented/precision_recall_curve.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ==========================
# Print Results
# ==========================

print("\nEvaluation Completed Successfully!\n")

print("Saved Files:")

print("runs/mobilenetv3_augmented/roc_curve.png")

print("runs/mobilenetv3_augmented/precision_recall_curve.png")

print("\nAverage Precision (AP) Scores:")

for i, name in enumerate(class_names):

    ap = average_precision_score(
        y_true_bin[:, i],
        y_score[:, i]
    )

    print(f"{name:<25}: {ap:.4f}")

print("\nDone.")