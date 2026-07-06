from __future__ import annotations

from dataclasses import dataclass

from phase4.app.augmentation import build_training_augmentation


@dataclass(frozen=True)
class ModelBuildResult:
    model: object
    backbone: object


def _get_backbone(tf, backbone: str, image_size: tuple[int, int], weights: str | None):
    normalized = backbone.lower().replace("-", "").replace("_", "")
    input_shape = (image_size[0], image_size[1], 3)
    if normalized in {"mobilenetv3small", "mobilenetv3"}:
        return tf.keras.applications.MobileNetV3Small(
            include_top=False,
            weights=weights,
            input_shape=input_shape,
            pooling="avg",
            include_preprocessing=True,
        )
    if normalized == "mobilenetv2":
        return tf.keras.applications.MobileNetV2(
            include_top=False,
            weights=weights,
            input_shape=input_shape,
            pooling="avg",
        )
    if normalized in {"efficientnetb0", "efficientnet"}:
        return tf.keras.applications.EfficientNetB0(
            include_top=False,
            weights=weights,
            input_shape=input_shape,
            pooling="avg",
        )
    raise ValueError(
        "Unsupported backbone. Use mobilenetv3small, mobilenetv2, or efficientnetb0. "
        "Exact EfficientNet-Lite0 can be introduced later if a local TensorFlow build "
        "or TF Hub source provides it."
    )


def _apply_backbone_preprocessing(tf, backbone_name: str, inputs):
    normalized = backbone_name.lower().replace("-", "").replace("_", "")
    if normalized == "mobilenetv2":
        return tf.keras.layers.Lambda(
            tf.keras.applications.mobilenet_v2.preprocess_input,
            name="mobilenetv2_preprocess",
        )(inputs)
    return inputs


def build_classifier(
    *,
    num_classes: int,
    image_size: tuple[int, int],
    backbone_name: str,
    dropout: float,
    learning_rate: float,
    weights: str | None = "imagenet",
    fine_tune_at: int | None = None,
) -> ModelBuildResult:
    try:
        import tensorflow as tf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("TensorFlow is required to build the training model.") from exc

    if num_classes < 2:
        raise ValueError("At least two crop-disease classes are required for training.")

    augmentation = build_training_augmentation(image_size)
    backbone = _get_backbone(tf, backbone_name, image_size, weights)
    backbone.trainable = fine_tune_at is not None
    if fine_tune_at is not None:
        for layer in backbone.layers[:fine_tune_at]:
            layer.trainable = False

    inputs = tf.keras.Input(shape=(image_size[0], image_size[1], 3), name="image")
    x = augmentation(inputs)
    x = _apply_backbone_preprocessing(tf, backbone_name, x)
    x = backbone(x, training=False)
    x = tf.keras.layers.Dropout(dropout, name="classifier_dropout")(x)
    outputs = tf.keras.layers.Dense(num_classes, activation="softmax", name="class_probabilities")(x)
    model = tf.keras.Model(inputs=inputs, outputs=outputs, name="plant_disease_classifier")
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=learning_rate),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return ModelBuildResult(model=model, backbone=backbone)
