from PIL import Image
import os
current_directory = os.getcwd()
DESTINATION_PATH = "/home/pi/photo-booth/server/static/thumbnails"

def generate_thumbnail(filename, size=(200, 200)):

    with Image.open(filename) as img:
        img.thumbnail(size)
        img.save(DESTINATION_PATH + '/' + os.path.basename(filename))
