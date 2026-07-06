import numpy as np
import matplotlib.pyplot as plt

# Confusion Matrix
cm = np.array([
    [148, 0, 2],
    [0, 80, 0],
    [0, 7, 143]
])

classes = [
    "Early Blight",
    "Healthy",
    "Late Blight"
]

plt.figure(figsize=(6,5))

plt.imshow(cm, interpolation='nearest', cmap='Blues')
plt.colorbar()

plt.xticks(np.arange(len(classes)), classes, rotation=15)
plt.yticks(np.arange(len(classes)), classes)

# Write values inside cells
for i in range(cm.shape[0]):
    for j in range(cm.shape[1]):
        plt.text(
            j,
            i,
            str(cm[i, j]),
            ha="center",
            va="center",
            color="white" if cm[i, j] > cm.max()/2 else "black",
            fontsize=12,
            fontweight="bold"
        )

plt.xlabel("Predicted Class", fontsize=12)
plt.ylabel("Actual Class", fontsize=12)
plt.title("Confusion Matrix", fontsize=14)

plt.tight_layout()

plt.savefig(
    "runs/mobilenetv3_augmented/confusion_matrix.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()

print("Confusion matrix saved successfully!")