from flask import request, render_template
from catsnap.batch.tag_batch import get_tags
from catsnap.batch.image_batch import get_images
from catsnap.image_truck import ImageTruck
from catsnap.table.tag import Tag
from catsnap.web import app

@app.route('/find', methods=['GET'])
def find():
    tag_names = request.args['find_tags'].split(' ')
    image_structs = []
    image_data = Tag.get_image_data(tag_names)
    for filename, image_tags in image_data:
        image_structs.append({
            'url': ImageTruck.url_for_filename(filename),
            'tags': ' '.join(image_tags)
        })
    return render_template('find.html', images=image_structs)
