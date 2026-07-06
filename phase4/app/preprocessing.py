from __future__ import annotations

from pathlib import Path
import struct

import numpy as np


def _import_cv2():
    try:
        import cv2  # type: ignore
    except ImportError as exc:
        raise RuntimeError("OpenCV is required for image preprocessing. Install opencv-python-headless.") from exc
    return cv2


def read_rgb_image(path: str | Path) -> np.ndarray:
    cv2 = _import_cv2()
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Unable to read image: {path}")
    return cv2.cvtColor(image, cv2.COLOR_BGR2RGB)


def read_image_dimensions(path: str | Path) -> tuple[int, int]:
    """Return (width, height), using OpenCV when present and PNG/JPEG headers otherwise."""
    try:
        image = read_rgb_image(path)
        return int(image.shape[1]), int(image.shape[0])
    except RuntimeError:
        pass

    data = Path(path).read_bytes()
    if data.startswith(b"\x89PNG\r\n\x1a\n") and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return int(width), int(height)
    if data.startswith(b"\xff\xd8"):
        index = 2
        while index + 9 < len(data):
            if data[index] != 0xFF:
                index += 1
                continue
            marker = data[index + 1]
            block_length = int.from_bytes(data[index + 2 : index + 4], "big")
            if marker in {0xC0, 0xC2}:
                height = int.from_bytes(data[index + 5 : index + 7], "big")
                width = int.from_bytes(data[index + 7 : index + 9], "big")
                return width, height
            index += 2 + block_length
    raise ValueError(f"Unable to determine image dimensions: {path}")


def resize_image(image_rgb: np.ndarray, image_size: tuple[int, int]) -> np.ndarray:
    cv2 = _import_cv2()
    height, width = image_size
    resized = cv2.resize(image_rgb, (width, height), interpolation=cv2.INTER_AREA)
    return resized.astype(np.float32)


def resize_and_normalize(image_rgb: np.ndarray, image_size: tuple[int, int]) -> np.ndarray:
    return resize_image(image_rgb, image_size) / 255.0


def preprocess_image_file(path: str | Path, image_size: tuple[int, int], normalize: bool = True) -> np.ndarray:
    image = read_rgb_image(path)
    if normalize:
        return resize_and_normalize(image, image_size)
    return resize_image(image, image_size)


def add_batch_dimension(image: np.ndarray) -> np.ndarray:
    if image.ndim != 3:
        raise ValueError(f"Expected HWC image, got shape {image.shape}")
    return np.expand_dims(image, axis=0).astype(np.float32)
