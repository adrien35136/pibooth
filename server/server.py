from flask import Flask, redirect,render_template, jsonify, url_for, send_from_directory, abort, Response
import os
import asyncio
from  thumbnail_utils import generate_thumbnail
from datetime import datetime
import inotify.adapters
import threading

app = Flask(__name__)

IMAGE_FOLDER = '/photos'
THUMBNAIL_FOLDER = 'static/thumbnails'

@app.route('/')
def index():
    return render_template('index.html')
    
@app.route('/get_images')
def get_images():
    images = []

    # Lister et trier les fichiers par date de modification décroissante
    files = sorted(
        [f for f in os.listdir(THUMBNAIL_FOLDER) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))],
        key=lambda x: os.path.getmtime(os.path.join(THUMBNAIL_FOLDER, x)),
        reverse=True
    )

    for filename in files:
        thumb_path = THUMBNAIL_FOLDER + '/' + filename
        full_path = "http://192.168.4.1:8000" + '/photos/' + filename

        images.append({
            'thumb': thumb_path,
            'full': full_path
        })

    return jsonify(images)
    
@app.route('/test')
def open_galerie():
    #return redirect ("open-broswer://toto@http://192.168.4.1:8000", code=302)
    js_redirect = """
    <head>
  <meta http-equiv="refresh" content="0; URL=http://192.168.4.1:8000">
  <script>
    window.location.href = "http://192.168.4.1:8000";
  </script>
</head>
"""
    return Response(js_redirect, mimetype="text/html")
    
@app.route('/generate_204')
def android_captive_portal():
    # Routine en javascript pour rediriger les utilisateur directement sur la galerie à partir du portail captif sur android
    js_redirect = """
    <html>
      <head>
        <script type="text/javascript">
        window.location.href = "intent://192.168.4.1:8000/#Intent;scheme=http;end";
        </script>
      </head>
      <body>
        Si vous n'êtes pas redirigé automatiquement, <a href="http://192.168.4.1:8000/">cliquez ici</a>.
      </body>
    </html>
    """

    return Response(js_redirect, mimetype="text/html")

# @app.route('/hotspot-detect.html')
# def apple_captive_portal():
    # # Routine en javascript pour rediriger les utilisateur directement sur la galerie à partir du portail captif sur ios
    # js_redirect = """
    # <html>
      # <head>
        # <script type="text/javascript">
          # window.location.href = "http://192.168.4.1:8000/";
        # </script>
      # </head>
      # <body>
        # Si vous n'êtes pas redirigé automatiquement, <a href="http://192.168.4.1:8000">cliquez ici</a>.
      # </body>
    # </html>
    # """

    # return Response(js_redirect, mimetype="text/html")
    
def main():
    # Lancer le worker dans un thread séparé
    app.run(host="0.0.0.0", port=8001, debug=True)

if __name__ == '__main__':
    main()
  
