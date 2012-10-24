from flask import request, render_template
from catsnap.batch.tag_batch import get_tags
from catsnap.batch.image_batch import get_images
from catsnap.image_truck import ImageTruck
from catsnap.web import app

@app.route('/find', methods=['GET'])
def find():
    tag_names = request.args['find_tags'].split(' ')
    filenames = set()
    tags = get_tags(tag_names)
    for tag in tags:
        filenames.update(tag['filenames'])
    images = get_images(filenames)
    image_structs = []
    for image in images:
        image_structs.append({
            'url': ImageTruck.url_for_filename(image['filename']),
            'tags': ' '.join(image['tags'])
        })
    return render_template('find.html', images=image_structs)
