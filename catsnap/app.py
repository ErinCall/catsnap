import os
from flask import Flask, render_template, request, g, session, redirect
from catsnap.image_truck import ImageTruck
from catsnap.batch.image_batch import get_images
from catsnap.batch.tag_batch import get_tags
from flask_openid import OpenID

app = Flask(__name__)
app.secret_key = os.environ['CATSNAP_SECRET_KEY']
oid = OpenID(app)

@app.before_request
def before_request():
    g.user = None
    if 'openid' in session:
        g.user = 1

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

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        openid = request.form.get('openid')
        if openid:
            return oid.try_login(openid, ask_for=['email'])

    return render_template('login.html', next=oid.get_next_url(),
                           error=oid.fetch_error())

@oid.after_login
def login_redirect(openid_response):
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',
            port=port,
            debug=os.environ.get('CATSNAP_DEBUG', False))
