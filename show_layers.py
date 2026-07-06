import tensorflow as tf

model = tf.keras.models.load_model(
    "phase4/runs/mobilenetv3_augmented/checkpoints/best.keras"
)

for i, layer in enumerate(model.layers):
    print(i, layer.name, layer.__class__.__name__)