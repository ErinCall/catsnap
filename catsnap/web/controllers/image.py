from __future__ import unicode_literals

import json
from flask import request, render_template, redirect, g, url_for
from requests.exceptions import RequestException
from sqlalchemy.exc import IntegrityError
from catsnap.image_truck import ImageTruck
from catsnap.table.image import Image, ImageResize, ImageContents
from catsnap.table.album import Album
from catsnap.web.formatted_routes import formatted_route, abort
from catsnap.web.utils import login_required
from catsnap.worker.tasks import process_image
from catsnap.worker.web import delay
from catsnap import Client


@formatted_route('/add', methods=['GET'])
@login_required
def show_add(request_format):
    session = Client().session()
    albums = session.query(Album).all()
    if request_format == 'html':
        return render_template('add.html.jinja', albums=albums)
    elif request_format == 'json':
        return {'albums': albums}


@formatted_route('/add', methods=['POST'])
@login_required
def add(request_format):
    url = request.form['url']

    if url:
        try:
            truck = ImageTruck.new_from_url(url)
        except RequestException:
            abort(request_format, 400, "That url is no good.")
    elif request.files['file']:
        data = request.files['file']
        truck = ImageTruck.new_from_stream(data.stream, data.mimetype)
    else:
        abort(request_format, 400, "Please submit either a file or a url.")

    session = Client().session()
    image = Image(filename=truck.filename, source_url=url)
    album_id = request.form.get('album_id')
    if album_id:
        image.album_id = int(album_id)
    else:
        image.album_id = None
    session.add(image)
    session.flush()
    contents = ImageContents(image_id=image.image_id,
                             contents=truck.contents,
                             content_type=truck.content_type)
    session.add(contents)
    session.flush()
    delay(process_image, contents.image_contents_id)

    if request_format == 'html':
        return redirect(url_for('show_image', image_id=image.image_id))
    elif request_format == 'json':
        return {'url': truck.url(), 'image_id': image.image_id}

@formatted_route(
    '/image/<int:image_id>', methods=['GET'], defaults={'size': 'medium'})
@formatted_route('/image/<int:image_id>/<size>', methods=['GET'])
def show_image(request_format, image_id, size):
    session = Client().session()
    image = session.query(Image).\
        filter(Image.image_id == image_id).\
        one()
    if g.user:
        albums = session.query(Album).all()
    else:
        albums = []
    if image.album_id is not None:
        album = session.query(Album).\
            filter(Album.album_id == image.album_id).\
            one()
    else:
        album = None
    (prev, next) = image.neighbors()
    resizes = session.query(ImageResize).\
        filter(ImageResize.image_id == image_id).\
        order_by(ImageResize.width.asc()).\
        all()
    url = ImageTruck.url_for_filename(image.filename)
    if resizes and size != 'original':
        if size not in map(lambda r: r.suffix, resizes):
            size = resizes[0].suffix
        url = '%s_%s' % (url, size)
    tags = image.get_tags()
    if request_format == 'html':
        return render_template('image.html.jinja',
                               image=image,
                               prev=prev,
                               next=next,
                               album=album,
                               albums=albums,
                               url=url,
                               tags=tags,
                               resizes=resizes,
                               size=size)
    elif request_format == 'json':
        return {
            'description': image.description,
            'title': image.title,
            'camera': image.camera,
            'photographed_at': image.photographed_at,
            'focal_length': image.focal_length,
            'aperture': image.aperture,
            'shutter_speed': image.shutter_speed,
            'iso': image.iso,
            'album_id': image.album_id,
            'tags': list(tags),
            'source_url': url,
        }


@formatted_route('/image/<image_id>', methods=['PATCH'])
@login_required
def edit_image(request_format, image_id):
    if request_format != 'json':
        abort(request_format, 400, "This endpoint is JSON-only...")

    session = Client().session()
    image = session.query(Image).\
        filter(Image.image_id == image_id).\
        one()

    if 'attributes' in request.form:
        attributes = json.loads(request.form['attributes'])
        for attribute, value in attributes.iteritems():
            if hasattr(image, attribute):
                if not value:
                    value = None
                setattr(image, attribute, value)
            else:
                return {
                    'status': 'error',
                    'error_description': "No such attribute '%s'" % attribute
                }

    if 'add_tag' in request.form:
        tag = request.form['add_tag']
        image.add_tags([tag])

    if 'remove_tag' in request.form:
        tag = request.form['remove_tag']
        image.remove_tag(tag)

    session.add(image)
    try:
        session.flush()
    except IntegrityError:
        return {
            'status': 'error',
            'error_description': "No such album_id '%s'" % image.album_id
        }

    return {'status': 'ok'}
