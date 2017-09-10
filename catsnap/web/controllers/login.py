

import bcrypt
from flask import session, redirect, render_template, request
from werkzeug.exceptions import BadRequest
from catsnap.web import app
from catsnap.web.utils import login_required
from catsnap.web.formatted_routes import formatted_route
from catsnap import Client

@app.route('/login', methods=['GET'])
def login():
    return render_template('login.html.jinja', next=request.args.get('next', ''))

@app.route('/login', methods=['POST'])
def do_login():
    try:
        password_hash = Client().config()['password_hash']
        if type(password_hash) == str:
            password_hash = password_hash.encode('utf-8')

        given_password = request.form['password'].strip()
        if type(given_password) == str:
            given_password = given_password.encode('utf-8')

        if bcrypt.hashpw(given_password, password_hash) == password_hash:
            session['logged_in'] = True
            return redirect(request.form.get('next', '/'))
        else:
            return render_template('login.html.jinja',
                                   error='Incorrect password.')
    except BadRequest:
        return render_template('login.html.jinja',
                               error='You must enter a password.')

@app.route('/logout', methods=['GET'])
def logout():
    if 'logged_in' in session:
        session.pop('logged_in')
    return redirect('/')
