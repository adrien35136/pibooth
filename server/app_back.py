from flask import Flask, redirect,render_template, jsonify, url_for, send_from_directory, abort
import os
import asyncio
from  thumbnail_utils import generate_thumbnail
from datetime import datetime
import inotify.adapters

app = Flask(__name__)



UPLOAD_FOLDER = '/media/pi/PHOTOMATON/photos'
CHECK_INTERVAL = 5  # secondes
# Chemin vers le dossier contenant les images
IMAGE_FOLDER = '/static/images'
THUMBNAIL_FOLDER = 'static/thumbnails'

async def monitor_upload_folder():
    while True:
        try:
            i = inotify.adapters.Inotify()
            i.add_watch(UPLOAD_FOLDER)
            for event in i.event_gen(yield_nones=False):
                (_, type_names, path, filename) = event
                print (type_names)
                if type_names[0] == 'IN_CLOSE_WRITE':
                    print (f"generate picture == {type_names}")
                    generate_thumbnail(path + '/' + filename)
        except Exception as e:
            print(f"Erreur dans le worker: {e}")
        await asyncio.sleep(CHECK_INTERVAL)


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_images')
def get_images():
    images = []
    for filename in os.listdir(THUMBNAIL_FOLDER):
        if filename.endswith(('.jpg', '.jpeg', '.png', '.gif')):
            images.append(os.path.join(THUMBNAIL_FOLDER, filename))
    return jsonify(images)

@app.route('/generate_204')
def android_captive_portal():
    return redirect(url_for('index'), code=302)

@app.route('/hotspot-detect.html')
def apple_captive_portal():
    return redirect(url_for('index'), code=302)

def start_worker():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(monitor_upload_folder())

if __name__ == '__main__':
    import threading
    # Lancer le worker dans un thread séparé
    threading.Thread(target=start_worker, daemon=True).start()
    app.run(host="0.0.0.0", port=8000, debug=True)
  
