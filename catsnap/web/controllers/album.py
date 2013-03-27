from __future__ import unicode_literals

from catsnap.web.formatted_routes import formatted_route
from flask import request, render_template, redirect, g, url_for
from catsnap import Client
from catsnap.table.album import Album

@formatted_route('/new_album', methods=['GET'])
def new_album(request_format):
    if request_format == 'html':
        return render_template('new_album.html', user=g.user)
    else:
        return {}

@formatted_route('/new_album', methods=['POST'])
def create_album(request_format):
    if not g.user:
        return redirect('/')
    session = Client().session()
    album = Album(name=request.form['name'])
    session.add(album)
    session.flush()

    if request_format == 'html':
        return redirect(url_for('show_add'))
    else:
        return {'album_id': album.album_id}

