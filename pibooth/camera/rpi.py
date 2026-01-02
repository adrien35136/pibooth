# -*- coding: utf-8 -*-

import time
from picamera2 import Picamera2, Preview
from libcamera import Transform
from PIL import Image
from pibooth.camera.base import BaseCamera
from pibooth.utils import LOGGER


def get_rpi_camera_proxy(port=None):
    """Return Picamera2 instance if a camera is available."""
    try:
        cameras = Picamera2.global_camera_info()
        if not cameras:
            return None
        if port is not None and port < len(cameras):
            return Picamera2(port)
        return Picamera2()
    except Exception:
        return None


class RpiCamera(BaseCamera):
    """Raspberry Pi Camera backend using Picamera2 + QTGL preview"""

    IMAGE_EFFECTS = ['none']

    def _specific_initialization(self):
        LOGGER.info("Initializing Picamera2 backend")

        # Create camera
        self._camera = get_rpi_camera_proxy()
        if self._camera is None:
            raise EnvironmentError("No Raspberry Pi camera detected")

        self._preview = None
        self._preview_started = False

        # Transform (flip)
        transform = Transform(hflip=self.capture_flip, vflip=False)

        # Preview config (LOW RES, GPU FAST)
        self._preview_config = self._camera.create_preview_configuration(
            main={
                "size": (1280, 960),
                "format": "YUV420"
            },
            transform=transform
        )

        # Capture config (FULL SENSOR)
        self._capture_config = self._camera.create_still_configuration(
            transform=transform
        )

        self._camera.configure(self._preview_config)
        self._camera.start()
        time.sleep(1.5)  # AWB / AE warmup

    # ---------------------------------------------------------------------

    def preview(self, window, flip=True):
        """Start GPU preview (QTGL)."""
        self._window = window

        if not self._preview_started:
            LOGGER.info("Starting Picamera2 preview (QTGL)")
            self._preview = self._camera.start_preview(Preview.QTGL)
            self._preview_started = True

    def preview_wait(self, timeout, alpha=60):
        """Let preview run while waiting."""
        time.sleep(timeout)

    def preview_countdown(self, timeout, alpha=60, flash_led=None):
        """Countdown handled by pygame (NOT camera)."""
        timeout = int(timeout)
        if timeout < 1:
            return

        while timeout > 0:
            self._window.show_countdown(timeout)
            time.sleep(1)
            timeout -= 1

        self._window.show_smile()
        time.sleep(0.5)

    def stop_preview(self):
        if self._preview_started:
            self._camera.stop_preview()
            self._preview_started = False
        self._window = None

    # ---------------------------------------------------------------------

    def capture(self, effect=None):
        """Capture full-resolution image."""
        self._camera.stop()
        self._camera.configure(self._capture_config)
        self._camera.start()

        array = self._camera.capture_array("main")
        image = Image.fromarray(array)
        self._captures.append((image, effect))

        # Restore preview
        self._camera.stop()
        self._camera.configure(self._preview_config)
        self._camera.start()

    # ---------------------------------------------------------------------

    def quit(self):
        if self._preview_started:
            self._camera.stop_preview()
        self._camera.stop()
        self._camera.close()
