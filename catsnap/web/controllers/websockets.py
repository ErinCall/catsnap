

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
        # this sleep is recommended by Kenneth Reitz; I believe it prevents
        # the thread from sucking down resources while waiting for a message.
        # His original comment was:
        # Sleep to prevent *constant* context-switches.
        gevent.sleep(0.1)
        message = websocket.receive()
        try:
            body = json.loads(message)
        except TypeError as ValueError:
            continue

        task_id = body['task_id']
        socket_bridge.register(
            websocket,
            lambda message: message.get('task_id') == task_id,
            lambda message: '_' + message['suffix']
                    if message['suffix'] != ''
                    else message['suffix']
        )
