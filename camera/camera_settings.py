"""
Paramètres typés pour le sous-système caméra (spec section 5/26).
"""
from dataclasses import dataclass

from core.constants import (
    DEFAULT_CAMERA_INDEX,
    DEFAULT_CAMERA_WIDTH,
    DEFAULT_CAMERA_HEIGHT,
    DEFAULT_CAMERA_FPS,
)


@dataclass
class CameraSettings:
    device_index: int = DEFAULT_CAMERA_INDEX
    width: int = DEFAULT_CAMERA_WIDTH
    height: int = DEFAULT_CAMERA_HEIGHT
    fps: int = DEFAULT_CAMERA_FPS

    @classmethod
    def from_dict(cls, data: dict) -> "CameraSettings":
        return cls(
            device_index=data.get("device", DEFAULT_CAMERA_INDEX),
            width=data.get("width", DEFAULT_CAMERA_WIDTH),
            height=data.get("height", DEFAULT_CAMERA_HEIGHT),
            fps=data.get("fps", DEFAULT_CAMERA_FPS),
        )

    def to_dict(self) -> dict:
        return {
            "device": self.device_index,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
        }
