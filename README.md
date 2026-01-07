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

# Fix problem when option is added in the menu to choose the template

After installed the package : pip3 install pibooth-picture-template

Removed the following fonction in "/home/adrien/.local/lib/python3.9/site-packages/pibooth_picture_template.py"

```
#@pibooth.hookimpl
#def pibooth_configure(cfg):
#    """Declare the new configuration options."""
#    cfg.add_option('PICTURE', 'template', 'picture_template.xml',
#                   "Pictures template path, it should contain 8 pages (4 capture numbers and 2 orientations)")
```


## Problem when starting Picamera Preview with full resolution (out of resources)

The Raspberry Pi's camera module relies on GPU memory for processing. By default, the Raspberry Pi allocates a small portion of memory to the GPU, which might not be enough for both Picamera and OpenCV to work together.
To increase GPU memory:
Open the Raspberry Pi configuration:
```
$ sudo raspi-config
```
Go to Performance Options -> GPU Memory.
Set the GPU memory to at least 256 MB (you may need more depending on the application requirements).


## Création d'un script sh pour activer les règles IPtables : /home/adrien/Documents/pibooth/server/iptables-boot.sh :

```sh
#!/bin/bash
iptables -t nat -A PREROUTING -i wlan0 -p tcp --dport 80 -j DNAT --to-destination 192.168.4.1:8000
```

Le rendre executable : 

sudo chmod +x  /home/adrien/Documents/pibooth/server/iptables-boot.sh

## Créez un service systemd pour lancer le script des règles iptables:

```
sudo nano /etc/systemd/system/iptables-startup.service
```

Copier le contenu ci-dessous : 
```
[Unit]
Description=Apply iptables NAT rule at startup
After=network.target

[Service]
ExecStart=/usr/local/bin/iptables-boot.sh
Type=oneshot
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
```

Activez et démarrez le service :

```
sudo systemctl enable iptables-startup.service
sudo systemctl start iptables-startup.service
```