import os
import time
import shutil
import psutil
from time import sleep

UPLOAD_FOLDER = '/media/adrien/PHOTOMATON/photos'
DEFAULT_PICTURES_PATH = "/home/adrien/Images/photos_pibooth"

def get_usb_key_mounted_path(label):
    timeout = 120  # Limite de temps pour attendre le montage de la clé USB
    elapsed_time = 0
    interval = 1  # Vérifier toutes les secondes
    while elapsed_time < timeout:
        print (f"elapsed_time == {elapsed_time}")
        # Parcourir toutes les partitions montées
        for partition in psutil.disk_partitions(all=False):
            # Vérifier si le chemin de montage contient "/media" (en général, les périphériques externes sont montés ici)
            if "/media" in partition.mountpoint:
                # Utiliser os.path.basename pour obtenir le nom du dossier de montage
                if label in os.path.basename(partition.mountpoint):
                    return partition.mountpoint
        sleep(interval)
        elapsed_time += interval
    return ""

def create_symlink_to_usb(label, symlink_path="/home/adrien/Documents/pibooth/server/photos"):
    usb_path = get_usb_key_mounted_path(label)
    if usb_path:
        print(f"Clé USB trouvée : {usb_path}")
        try:
            if os.path.islink(symlink_path) or os.path.exists(symlink_path):
                os.remove(symlink_path)
            os.symlink(usb_path, symlink_path)
            print(f"Lien symbolique créé : {symlink_path} → {usb_path}")
        except Exception as e:
            print(f"Erreur lors de la création du lien symbolique : {e}")
    else:
        print(f"Clé USB non trouvée -> Set default path = {DEFAULT_PICTURES_PATH}")
        try:
            if os.path.islink(symlink_path) or os.path.exists(symlink_path):
                os.remove(symlink_path)
            os.symlink(DEFAULT_PICTURES_PATH, symlink_path)
            print(f"Lien symbolique créé : {symlink_path} → {DEFAULT_PICTURES_PATH}")
        except Exception as e:
            print(f"Erreur lors de la création du lien symbolique : {e}")

if __name__ == '__main__':
    
    create_symlink_to_usb("PHOTOMATON")


