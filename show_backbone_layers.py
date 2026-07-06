import tensorflow as tf

model = tf.keras.models.load_model(
    "phase4/runs/mobilenetv3_augmented/checkpoints/best.keras"
)

backbone = model.get_layer("MobileNetV3Small")

print("="*80)
print(backbone.name)
print("="*80)

for i, layer in enumerate(backbone.layers[-30:]):
    print(i, layer.name, layer.__class__.__name__)