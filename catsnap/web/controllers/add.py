from flask import request, render_template, redirect, g
from catsnap.image_truck import ImageTruck
from catsnap.document.image import Image
from catsnap.batch.tag_batch import add_image_to_tags
from catsnap.web import app

@app.route('/add', methods=['POST'])
def add():
    if not g.user:
        return redirect('/')
    tag_names = request.form['add_tags'].split(' ')
    url = request.form['url']

    truck = ImageTruck.new_from_url(url)
    truck.upload()
    image = Image(truck.calculate_filename(), url)
    image.add_tags(tag_names)
    add_image_to_tags(truck.calculate_filename(), tag_names)

    return render_template('added.html', url=truck.url())
