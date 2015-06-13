import os
if os.environ.get('ENV') and os.path.exists(os.environ['ENV']):
    for line in open(os.environ['ENV']):
        var = line.strip().split('=')
        if len(var) == 2:
            os.environ[var[0]] = var[1]


from catsnap.web import app
import sys

if __name__ == '__main__':
    sys.stderr.write(
"""WARNING: The server can't accept websocket connections when invoked this way.
Use `gunicorn -k flask_sockets.worker -b 0.0.0.0:5000 catsnap.app:app` instead.
""")
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0',
            port=port,
            debug=os.environ.get('CATSNAP_DEBUG', False))
