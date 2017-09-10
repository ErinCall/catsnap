import json
from flask import request, render_template, redirect, g, url_for
from requests.exceptions import RequestException
from sqlalchemy.exc import IntegrityError
from catsnap.image_truck import ImageTruck, TryHTTPError
from catsnap.table.image import Image, ImageResize, ImageContents
from catsnap.table.album import Album
from catsnap.web import app
from catsnap.web.formatted_routes import formatted_route, abort
from catsnap.web.utils import login_required
from catsnap.worker.tasks import process_image
from catsnap.db_redis_coordination import delay
from catsnap import Client


@formatted_route('/add', methods=['GET'])
@login_required
def show_add(request_format):
    session = Client().session()
    albums = session.query(Album).all()
    if request_format == 'html':
        return render_template('add.html.jinja', albums=albums)
    elif request_format == 'json':
        return {'albums': albums}


@formatted_route('/add', methods=['POST'])
@login_required
def add(request_format):
    url = request.form.get('url')

    if url:
        try:
            trucks = [ImageTruck.new_from_url(url)]
        except RequestException:
            abort(request_format, 400, "That url is no good.")
        except TryHTTPError:
            abort(request_format,
                  400,
                  "Catsnap couldn't establish an HTTPS connection to that "
                  "image. An HTTP connection may succeed (this is a problem "
                  "on Catsnap's end, not something you did wrong).")
    elif request.files.get('file[]'):
        trucks = [ImageTruck.new_from_stream(data.stream)
                  for data in request.files.getlist('file[]')]
    elif request.files.get('file'):
        data = request.files['file']
        trucks = [ImageTruck.new_from_stream(data.stream)]
    else:
        abort(request_format, 400, "Please submit either a file or a url.")

    # These loops are sorta awkwardly phrased to avoid lots of round-tripping
    # to the database. I hope you don't consider the optimization premature.
    session = Client().session()
    images = []
    for truck in trucks:
        image = Image(filename=truck.filename, source_url=url)
        album_id = request.form.get('album_id')
        if album_id:
            image.album_id = int(album_id)
        session.add(image)
        images.append(image)

    session.flush()
    contentses = []
    for i in range(0, len(images)):
        (truck, image) = trucks[i], images[i]
        contents = ImageContents(image_id=image.image_id,
                                 contents=truck.contents,
                                 content_type=truck.content_type)
        session.add(contents)
        contentses.append(contents)
    session.flush()

    task_ids = []
    # Hey, this is a loop around a round-trip to redis. Although the Python
    # Redis library offers a way to send multiple requests in one thwack,
    # Celery doesn't appear to offer a way to use it. Nothing to be done.
    for contents in contentses:
        task_ids.append(delay(g.queued_tasks,
                              process_image,
                              contents.image_contents_id))

    if request_format == 'html':
        return redirect(url_for('show_image_html', image_id=image.image_id))
    elif request_format == 'json':
        return [{
                'url': trucks[i].url(),
                'image_id': images[i].image_id,
                'task_id': task_ids[i],
            } for i in range(0, len(trucks))]


# So....this is a bummer.
# Since upgrading Flask from 0.9 to 0.12, actions can no longer have multiple
# @formatted_route decorators. show_image can be accessed as either /image
# or /image/size, so the response-format difference has to be managed
# manually, by using separate functions per response-type.
# BEGIN bummer

@app.route('/image/<int:image_id>.json', defaults={'size': 'medium'})
@app.route('/image/<int:image_id>/<size>.json')
def show_image_json(image_id, size):
    try:
        response_data = show_image(image_id, size)
    except NoResultFound:
        flask_abort(make_response(
            json.dumps({error: 'Not Found', 'status': 'error'}),
            404,
            {'Content-Type': 'application/json'}))

    image = response_data['image']
    return json.dumps({
        'description': image.description,
        'title': image.title,
        'camera': image.camera,
        'photographed_at': image.photographed_at,
        'focal_length': image.focal_length,
        'aperture': image.aperture,
        'shutter_speed': image.shutter_speed,
        'iso': image.iso,
        'album_id': image.album_id,
        'tags': response_data['tags'],
        'source_url': response_data['url'],
    })

@app.route('/image/<int:image_id>.html', defaults={'size': 'medium'})
@app.route('/image/<int:image_id>/<size>.html')
@app.route('/image/<int:image_id>', defaults={'size': 'medium'})
@app.route('/image/<int:image_id>/<size>')
def show_image_html(image_id, size):
    response_data = show_image(image_id, size)
    return render_template('image.html.jinja', **response_data)


def show_image(image_id, size):
    session = Client().session()
    image = session.query(Image).\
        filter(Image.image_id == image_id).\
        one()
    if g.user:
        albums = session.query(Album).all()
    else:
        albums = []
    if image.album_id is not None:
        album = session.query(Album).\
            filter(Album.album_id == image.album_id).\
            one()
    else:
        album = None
    (prev, next) = image.neighbors()
    resizes = session.query(ImageResize).\
        filter(ImageResize.image_id == image_id).\
        order_by(ImageResize.width.asc()).\
        all()
    url = ImageTruck.url_for_filename(image.filename)

    if resizes and size in [r.suffix for r in resizes]:
        url = '{0}_{1}'.format(url, size)

    tags = image.get_tags()

    return dict(
        image=image,
        prev=prev,
        next=next,
        album=album,
        albums=albums,
        url=url,
        tags=list(tags),
        metadata_fields=[x__ for x__ in Image.metadata_fields if getattr(image, x__[0])],
        getattr=getattr,
        resizes=resizes,
        size=size)

# END bummer

@formatted_route('/image/<int:image_id>', methods=['PATCH'])
@login_required
def edit_image(request_format, image_id):
    if request_format != 'json':
        abort(request_format, 400, "This endpoint is JSON-only...")

    session = Client().session()
    image = session.query(Image).\
        filter(Image.image_id == image_id).\
        one()

    for attribute, value in request.form.items():
        if attribute in ['add_tag', 'remove_tag']:
            continue

        if hasattr(image, attribute):
            if attribute in ['album_id', 'title', 'description']:
                if not value:
                    value = None
                setattr(image, attribute, value)
            else:
                abort(request_format, 400, "'{0}' is read-only".format(attribute))
        else:
            abort(request_format, 400, "No such attribute '{0}'".format(attribute))

    if 'add_tag' in request.form:
        tag = request.form['add_tag']
        image.add_tags([tag])

    if 'remove_tag' in request.form:
        tag = request.form['remove_tag']
        image.remove_tag(tag)

    session.add(image)
    try:
        session.flush()
    except IntegrityError:
        abort(request_format, 404, "No such album_id '{0}'".format(image.album_id))

    return {
        'status': 'ok',
        'image': {
            'album_id': image.album_id,
            'title': image.title,
            'caption': image.caption(),
            'description': image.description,
            'tags': list(image.get_tags()),
        }
    }

@formatted_route('/image/reprocess/<int:image_id>', methods=['POST'])
@login_required
def reprocess_image(request_format, image_id):
    session = Client().session()
    image = session.query(Image).filter(Image.image_id == image_id).one()

    truck = ImageTruck.new_from_image(image)
    contents = ImageContents(image_id=image.image_id,
                             contents=truck.contents,
                             content_type=truck.content_type)

    session.add(contents)
    session.flush()
    delay(g.queued_tasks, process_image, contents.image_contents_id)

    if request_format == 'json':
        return {'status': 'ok'}
    else:
        return redirect(url_for('show_image', image_id=image.image_id))
