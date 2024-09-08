# PIBOOTH 

## To add a shutdown push button and LED status

Add the following to your /boot/config.txt and reboot:

```
# Configure gpio to shutdown the pi with push button
dtoverlay=gpio-shutdown,gpio_pin=20
# Configure LED pin to show the status of the pi
gpio=21=op,dh
```

## Resolve touch screen problems

Add the following to your /boot/config.txt and reboot: `hdmi_blanking=1`

# Ajouter un plugin dans pibooth

Exemple: Déplacer le plugin "pibooth_getready_text.py" situé dans le repertoire "/docs/sources" dans le repertoire pibooth/plugins
Mettre ensuite le chemin du plugin dans le ficher de config pour qu'il soit prit en compte (.config/pibooth/pibooth.cfg):
plugins = "/home/adrien/Documents/pibooth/pibooth/plugins/pibooth_getready_text.py

## Problem when starting Picamera Preview with full resolution (out of resources)

The Raspberry Pi's camera module relies on GPU memory for processing. By default, the Raspberry Pi allocates a small portion of memory to the GPU, which might not be enough for both Picamera and OpenCV to work together.
To increase GPU memory:
Open the Raspberry Pi configuration:
$ sudo raspi-config
Go to Performance Options -> GPU Memory.
Set the GPU memory to at least 256 MB (you may need more depending on the application requirements).
