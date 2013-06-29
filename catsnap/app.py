import os
from flask import g, session, redirect
from catsnap.web import app

if os.environ.get('CATSNAP_BACKDOOR'):
    @app.route('/become_logged_in')
    def become_logged_in():
        g.user = 1
        session['openid'] = 'booya'
        return redirect('/')


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',
            port=port,
            debug=os.environ.get('CATSNAP_DEBUG', False))
