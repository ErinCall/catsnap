from __future__ import unicode_literals

from flask import request, render_template, make_response
from catsnap.image_truck import ImageTruck
from catsnap.table.tag import Tag
from catsnap.web.formatted_routes import formatted_route

@formatted_route('/find', methods=['GET'])
def find(request_format):
    tag_names = request.args['tags'].split(' ')
    image_structs = []
    image_data = Tag.get_image_data(tag_names)
    for filename, image_tags in image_data:
        image_structs.append({
            'url': ImageTruck.url_for_filename(filename),
            'tags': image_tags
        })
    if request_format == 'html':
        for struct in image_structs:
            struct['tags'] = ' '.join(struct['tags'])
        return render_template('find.html', images=image_structs)
    elif request_format == 'json':
        return image_structs
