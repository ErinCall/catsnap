from __future__ import unicode_literals

from flask import request, render_template, redirect, g
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

    truck = ImageTruck.new_from_url(url)
    truck.upload()
    session = Client().session()
    image = Image(filename=truck.calculate_filename(), source_url=url)
    session.add(image)
    image.add_tags(tag_names)

    if request_format == 'html':
        return render_template('added.html', url=truck.url())
    elif request_format == 'json':
        return {'url': truck.url()}
