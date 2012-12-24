from flask import request, render_template, redirect, g
from catsnap.image_truck import ImageTruck
from catsnap.table.image import Image
from catsnap.web import app
from catsnap import Client

@app.route('/add', methods=['POST'])
def add():
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

    return render_template('added.html', url=truck.url())
