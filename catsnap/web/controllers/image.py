from __future__ import unicode_literals

from flask import request, render_template, redirect, g, abort
from catsnap.image_truck import ImageTruck
from catsnap.resize_image import ResizeImage
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
        print 'fetching from remote url'
        truck = ImageTruck.new_from_url(url)
    elif request.files['file']:
        image = request.files['file']
        truck = ImageTruck.new_from_stream(image.stream, image.mimetype)
    else:
        abort(400)
    print 'uploading to s3'
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

    ResizeImage.make_resizes(image, truck)

    if request_format == 'html':
        return render_template('added.html', url=truck.url(), caption=image.caption())
    elif request_format == 'json':
        return {'url': truck.url()}

@formatted_route('/image/<image_id>', methods=['GET'])
def show_image(request_format, image_id):
    session = Client().session()
    image = session.query(Image).\
            filter(Image.image_id==image_id).\
            first()
    url = ImageTruck.url_for_filename(image.filename)
    tags = image.get_tags()
    if request_format == 'html':
        return render_template('image.html', image=image, url=url, tags=tags)
    elif request_format == 'json':
        return {
            'description': image.description,
            'title': image.title,
            'album_id': image.album_id,
            'tags': list(tags),
            'source_url': url,
                }
