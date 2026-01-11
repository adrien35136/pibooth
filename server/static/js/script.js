$(document).ready(function() {
    let currentIndex = 0;
    const imagesPerLoad = 12;
    let allImages = [];

    // Fonction pour charger la liste des images depuis le serveur
    function fetchImages() {
        $.get('/get_images', function(data) {
            allImages = data;
            loadImages();
        });
    }

    // Fonction pour charger les images
    function loadImages() {
        const gallery = $('#gallery');
        for (let i = currentIndex; i < currentIndex + imagesPerLoad && i < allImages.length; i++) {
            const imgUrl = allImages[i];
            const galleryItem = $('<a>').attr('href', imgUrl).attr('data-pswp-width', '1200').attr('data-pswp-height', '800').attr('target', '_blank');
            const img = $('<img>').attr('src', imgUrl).attr('alt', '');
            galleryItem.append(img);
            gallery.append(galleryItem);
        }
        currentIndex += imagesPerLoad;
        initPhotoSwipe();
    }

    // Initialiser PhotoSwipe
    function initPhotoSwipe() {
        let pswpElement = document.querySelectorAll('.pswp')[0];

        $('#gallery a').click(function(e) {
            e.preventDefault();

            let items = [];
            $('#gallery a').each(function() {
                items.push({
                    src: $(this).attr('href'),
                    w: parseInt($(this).attr('data-pswp-width')),
                    h: parseInt($(this).attr('data-pswp-height'))
                });
            });

            let options = {
                index: $('#gallery a').index(this),
                bgOpacity: 0.7,
                showHideOpacity: true
            };

            let lightBox = new PhotoSwipe(pswpElement, PhotoSwipeUI_Default, items, options);
            lightBox.init();
        });
    }

    // Charger la liste des images depuis le serveur
    fetchImages();

    // Charger plus d'images
    $('#load-more').click(function() {
        loadImages();
    });
});
