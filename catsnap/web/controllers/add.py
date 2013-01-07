from __future__ import unicode_literals

from flask import request, render_template, redirect, g, abort
from catsnap.image_truck import ImageTruck
from catsnap.table.image import Image
from catsnap.web.formatted_routes import formatted_route
from catsnap import Client

@formatted_route('/add', methods=['POST'])
def add(request_format):
    if not g.user:
        return redirect('/')
    tag_names = request.form['add_tags'].split(' ')
    url = request.form['url']

    if url:
        truck = ImageTruck.new_from_url(url)
    elif request.files['image_file']:
        image = request.files['image_file']
        truck = ImageTruck.new_from_stream(image.stream, image.mimetype)
    else:
        abort(400)
    truck.upload()
    session = Client().session()
    image = Image(filename=truck.calculate_filename(), source_url=url)
    session.add(image)
    image.add_tags(tag_names)

    if request_format == 'html':
        return render_template('added.html', url=truck.url())
    elif request_format == 'json':
        return {'url': truck.url()}
