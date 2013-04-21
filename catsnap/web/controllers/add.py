from __future__ import unicode_literals

from flask import request, render_template, redirect, g, abort
from catsnap.image_truck import ImageTruck
from catsnap.table.image import Image
from catsnap.table.album import Album
from catsnap.web.formatted_routes import formatted_route
from catsnap.web.utils import login_required
from catsnap import Client

@formatted_route('/add', methods=['GET'])
def show_add(request_format):
    session = Client().session()
    albums = session.query(Album).all()
    if request_format == 'html':
        return render_template('add.html', user=g.user, albums=albums)
    elif request_format == 'json':
        return {'albums': albums}

@formatted_route('/add', methods=['POST'])
@login_required
def add(request_format):
    tag_names = request.form['tags'].split(' ')
    url = request.form['url']

    if url:
        truck = ImageTruck.new_from_url(url)
    elif request.files['file']:
        image = request.files['file']
        truck = ImageTruck.new_from_stream(image.stream, image.mimetype)
    else:
        abort(400)
    truck.upload()
    session = Client().session()
    image = Image(filename=truck.calculate_filename(),
                  source_url=url,
                  description=request.form.get('description'),
                  title=request.form.get('title'))
    album_id = request.form['album']
    if album_id:
        image.album_id = album_id
    session.add(image)
    image.add_tags(tag_names)

    if request_format == 'html':
        return render_template('added.html', url=truck.url(), caption=image.caption())
    elif request_format == 'json':
        return {'url': truck.url()}
