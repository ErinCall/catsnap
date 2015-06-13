from __future__ import unicode_literals

import json
import gevent
from flask_sockets import Sockets
from catsnap.web import app
from catsnap import Client
from catsnap.worker.redis_websocket_bridge import REDIS_CHANNEL, \
                                                  RedisWebsocketBridge

sockets = Sockets(app)
socket_bridge = RedisWebsocketBridge()

@sockets.route('/task_info')
def task_info(websocket):
    while not websocket.closed:
        # this sleep is recommended by Kenneth Reitz; he says:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = websocket.receive()
        try:
            body = json.loads(message)
        except TypeError, ValueError:
            continue

        task_id = body['task_id']
        socket_bridge.register((
            websocket,
            lambda message: message.get('task_id') == task_id,
            lambda message: '_' + message['suffix']
                    if message['suffix'] != ''
                    else message['suffix']
        ))
