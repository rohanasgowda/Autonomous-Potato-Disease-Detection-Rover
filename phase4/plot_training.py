import pandas as pd
import matplotlib.pyplot as plt

# Read training history
df = pd.read_csv("runs/mobilenetv3_augmented/training_history.csv")

# ---------------- Accuracy Plot ----------------
plt.figure(figsize=(7,5))

plt.plot(df["epoch"], df["accuracy"], linewidth=2,
         label="Training Accuracy")

plt.plot(df["epoch"], df["val_accuracy"], linewidth=2,
         label="Validation Accuracy")

plt.xlabel("Epoch")
plt.ylabel("Accuracy")
plt.title("Training and Validation Accuracy")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    "runs/mobilenetv3_augmented/accuracy_plot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

# ---------------- Loss Plot ----------------
plt.figure(figsize=(7,5))

plt.plot(df["epoch"], df["loss"], linewidth=2,
         label="Training Loss")

plt.plot(df["epoch"], df["val_loss"], linewidth=2,
         label="Validation Loss")

plt.xlabel("Epoch")
plt.ylabel("Loss")
plt.title("Training and Validation Loss")
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.savefig(
    "runs/mobilenetv3_augmented/loss_plot.png",
    dpi=300,
    bbox_inches="tight"
)

plt.close()

print("Graphs generated successfully!")