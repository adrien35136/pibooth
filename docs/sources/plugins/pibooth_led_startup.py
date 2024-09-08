"""Plugin to manage the RGB lights via GPIO."""

import pibooth
from gpiozero import LED

__version__ = "1.0.0"

@pibooth.hookimpl
def pibooth_configure(cfg):
    cfg.add_option('CONTROLS', 'startup_led_pin', 29,
                    "Physical GPIO OUT pin to light a LED at pibooth startup")

@pibooth.hookimpl
def pibooth_startup(cfg, app):
    app.led_startup = LED("BOARD" + cfg.get('CONTROLS', 'startup_led_pin'))
