import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import cv2

MODEL_PATH = "runs/mobilenetv3_augmented/checkpoints/best.keras"

IMAGE_PATH = r"../dataset/test/potato_healthy/original (1121).jpg"

IMG_SIZE = (224,224)

model = tf.keras.models.load_model(MODEL_PATH)

backbone = model.get_layer("MobileNetV3Small")

grad_model = tf.keras.models.Model(
    [backbone.input],
    [backbone.get_layer("conv_1").output,
     backbone.output]
)

img = tf.keras.preprocessing.image.load_img(
    IMAGE_PATH,
    target_size=IMG_SIZE
)

img = tf.keras.preprocessing.image.img_to_array(img)
img = np.expand_dims(img,0)

with tf.GradientTape() as tape:

    backbone_output = backbone(img)

    conv_outputs,preds = grad_model(backbone_output)

    class_index=tf.argmax(preds[0])

    loss=preds[:,class_index]

grads=tape.gradient(loss,conv_outputs)

pooled_grads=tf.reduce_mean(grads,axis=(0,1,2))

conv_outputs=conv_outputs[0]

heatmap=conv_outputs@pooled_grads[...,tf.newaxis]

heatmap=tf.squeeze(heatmap)

heatmap=np.maximum(heatmap,0)

heatmap/=np.max(heatmap)

heatmap=cv2.resize(heatmap.numpy(),IMG_SIZE)

original=cv2.imread(IMAGE_PATH)

original=cv2.resize(original,IMG_SIZE)

heatmap=np.uint8(255*heatmap)

heatmap=cv2.applyColorMap(heatmap,cv2.COLORMAP_JET)

overlay=cv2.addWeighted(original,0.6,heatmap,0.4,0)

plt.figure(figsize=(12,4))

plt.subplot(131)
plt.imshow(cv2.cvtColor(original,cv2.COLOR_BGR2RGB))
plt.title("Original")
plt.axis("off")

plt.subplot(132)
plt.imshow(cv2.cvtColor(heatmap,cv2.COLOR_BGR2RGB))
plt.title("Grad-CAM")
plt.axis("off")

plt.subplot(133)
plt.imshow(cv2.cvtColor(overlay,cv2.COLOR_BGR2RGB))
plt.title("Overlay")
plt.axis("off")

plt.tight_layout()

plt.savefig(
    "gradcam_result.png",
    dpi=300
)

plt.show()