from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import shutil
import time
from uuid import uuid4


class CameraCaptureError(RuntimeError):
    """Raised when a camera image cannot be captured."""


@dataclass(frozen=True)
class CaptureResult:
    session_id: str
    image_path: Path


def generate_session_id() -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    return f"sess_{stamp}_{uuid4().hex[:6]}"


class CameraCapture:
    def __init__(
        self,
        capture_dir: str | Path,
        camera_index: int = 0,
        warmup_seconds: float = 0.2,
    ) -> None:
        self.capture_dir = Path(capture_dir)
        self.camera_index = camera_index
        self.warmup_seconds = max(0.0, warmup_seconds)

    def capture(self, session_id: str, source_image: str | Path | None = None) -> CaptureResult:
        self.capture_dir.mkdir(parents=True, exist_ok=True)
        if source_image is not None:
            return self._copy_source_image(session_id, Path(source_image))
        return CaptureResult(
            session_id=session_id,
            image_path=self._capture_camera_image(session_id),
        )

    def _copy_source_image(self, session_id: str, source_image: Path) -> CaptureResult:
        if not source_image.exists():
            raise CameraCaptureError(f"Source image was not found: {source_image}")
        suffix = source_image.suffix or ".jpg"
        target = self.capture_dir / f"{session_id}{suffix}"
        if source_image.resolve() != target.resolve():
            shutil.copy2(source_image, target)
        return CaptureResult(session_id=session_id, image_path=target)

    def _capture_camera_image(self, session_id: str) -> Path:
        target = self.capture_dir / f"{session_id}.jpg"
        try:
            self._capture_with_picamera2(target)
            return target
        except Exception as picamera_error:
            try:
                self._capture_with_opencv(target)
                return target
            except Exception as opencv_error:
                raise CameraCaptureError(
                    "Unable to capture image with Picamera2 or OpenCV."
                ) from opencv_error or picamera_error

    def _capture_with_picamera2(self, target: Path) -> None:
        from picamera2 import Picamera2  # type: ignore

        camera = Picamera2()
        try:
            camera.start()
            if self.warmup_seconds:
                time.sleep(self.warmup_seconds)
            camera.capture_file(str(target))
        finally:
            camera.stop()

    def _capture_with_opencv(self, target: Path) -> None:
        import cv2  # type: ignore

        camera = cv2.VideoCapture(self.camera_index)
        try:
            if not camera.isOpened():
                raise CameraCaptureError(f"Camera index {self.camera_index} is not available.")
            if self.warmup_seconds:
                time.sleep(self.warmup_seconds)
            ok, frame = camera.read()
            if not ok or frame is None:
                raise CameraCaptureError("OpenCV camera returned no frame.")
            if not cv2.imwrite(str(target), frame):
                raise CameraCaptureError(f"OpenCV could not write image: {target}")
        finally:
            camera.release()

