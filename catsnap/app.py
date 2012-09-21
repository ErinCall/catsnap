import os
from flask import Flask, render_template, request
from catsnap.image_truck import ImageTruck
from catsnap.batch.image_batch import get_images
from catsnap.batch.tag_batch import get_tags

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/find')
def find():
    tag_names = request.args['tags'].split(' ')
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

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',
            port=port,
            debug=os.environ.get('CATSNAP_DEBUG', False))
