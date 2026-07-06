from __future__ import annotations


def build_training_augmentation(image_size: tuple[int, int]):
    """Return lightweight Keras augmentation layers aligned with field-image variation."""
    try:
        import tensorflow as tf  # type: ignore
    except ImportError as exc:
        raise RuntimeError("TensorFlow is required for training augmentation.") from exc

    return tf.keras.Sequential(
        [
            tf.keras.layers.RandomFlip("horizontal"),
            tf.keras.layers.RandomRotation(0.08),
            tf.keras.layers.RandomZoom(height_factor=(-0.08, 0.08), width_factor=(-0.08, 0.08)),
            tf.keras.layers.RandomContrast(0.12),
            tf.keras.layers.RandomBrightness(0.12),
            tf.keras.layers.Resizing(image_size[0], image_size[1]),
        ],
        name="field_safe_augmentation",
    )

