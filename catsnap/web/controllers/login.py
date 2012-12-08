from flask import g, redirect, render_template, request, session
from catsnap.web import app
from catsnap.web import oid
from catsnap.config import MetaConfig

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    if request.method == 'POST':
        return oid.try_login(MetaConfig().owner_id,
                             ask_for=['email'])

    return render_template('login.html', next=oid.get_next_url(),
                           error=oid.fetch_error())

@oid.after_login
def login_redirect(openid_response):
    g.user = 1
    session['openid'] = openid_response.identity_url
    return redirect('/')

@app.route('/logout', methods=['GET', 'POST'])
def logout():
    if 'openid' in session:
        session.pop('openid')
    return redirect('/')
