from catsnap.web.formatted_routes import formatted_route, abort
from catsnap.web.utils import login_required
from flask import request, render_template, redirect, url_for
from sqlalchemy.exc import IntegrityError
from catsnap import Client
from catsnap.table.album import Album
from catsnap.image_truck import ImageTruck

@formatted_route('/new_album', methods=['GET'])
def new_album(request_format):
    if request_format == 'html':
        return render_template('new_album.html.jinja')
    else:
        return {}

@formatted_route('/new_album', methods=['POST'])
@login_required
def create_album(request_format):
    session = Client().session()
    album = Album(name=request.form['name'].strip())
    session.add(album)
    try:
        session.flush()
    except IntegrityError:
        session.rollback()
        abort(request_format, 409, "There is already an album with that name.")

    if request_format == 'html':
        return redirect(url_for('show_add'))
    else:
        return {'album_id': album.album_id}

@formatted_route('/album/<int:album_id>', methods=['GET'])
def view_album(request_format, album_id):
    album = Client().session().query(Album).\
            filter(Album.album_id == album_id).\
            one()
    images = Album.images_for_album_id(album_id)
    def struct_from_image(image):
        return {
            'page_url': url_for('show_image_html', image_id=image.image_id),
            'source_url': ImageTruck.url_for_filename(image.filename),
            'caption': image.caption(),
        }
    image_structs = list(map(struct_from_image, images))

    if request_format == 'html':
        return render_template('view_album.html.jinja',
                images=image_structs,
                album=album)
    else:
        return image_structs

