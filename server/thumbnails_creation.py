import inotify.adapters
from thumbnail_utils import generate_thumbnail
import os
import time
import shutil
import psutil
from time import sleep

UPLOAD_FOLDER = '/media/adrien/PHOTOMATON/photos'
DEFAULT_PICTURES_PATH = "/home/adrien/Images/photos_pibooth/photos"
CHECK_INTERVAL = 5  # secondes
THUMBNAILS_FOLDER = "/home/adrien/Documents/pibooth/server/static/thumbnails"

def monitor_upload_folder(path_to_save_pictures):
#def monitor_upload_folder():
    while True:
        try:
            i = inotify.adapters.Inotify()
            i.add_watch(path_to_save_pictures)
            print("Monitoring folder...")
            for event in i.event_gen(yield_nones=False):
                (_, type_names, path, filename) = event
                if 'IN_CLOSE_WRITE' in type_names:
                    try:
                        full_path = os.path.join(path, filename)
                        generate_thumbnail(full_path)
                        print(f"Thumbnail generated for: {filename}")
                    except Exception as e:
                        print(f"Erreur génération miniature: {e}")
        except Exception as e:
            print(f"Erreur dans le worker: {e}")
            time.sleep(CHECK_INTERVAL)  # éviter boucle trop rapide en cas d’erreur

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


def reset_thumbnails_folder():
    # Supprime le dossier s'il existe
    if os.path.exists(THUMBNAILS_FOLDER):
        try:
            shutil.rmtree(THUMBNAILS_FOLDER)
            print(f"Dossier existant supprimé : {THUMBNAILS_FOLDER}")
        except Exception as e:
            print(f"Erreur lors de la suppression : {e}")
            return

    # Crée le dossier (vide)
    try:
        os.makedirs(THUMBNAILS_FOLDER)
        print(f"Dossier créé : {THUMBNAILS_FOLDER}")
    except Exception as e:
        print(f"Erreur lors de la création : {e}")

if __name__ == '__main__':
   
    # Check if the USB key with the label "PHOTOMATON" is mounted
    path_usb_key_mounted = get_usb_key_mounted_path("PHOTOMATON")
        
    if os.path.exists(path_usb_key_mounted):
        path_to_save_pictures = path_usb_key_mounted + '/photos'
    else:
        path_to_save_pictures = DEFAULT_PICTURES_PATH
    
    print (path_to_save_pictures)

    monitor_upload_folder(path_to_save_pictures)
    #monitor_upload_folder()

