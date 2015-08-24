from __future__ import unicode_literals, absolute_import

import gevent
import json
import redis as redislib
from catsnap import Client
from catsnap.singleton import Singleton
from geventwebsocket.exceptions import WebSocketError

redis = redislib.from_url(Client().config()['redis_url'])
REDIS_CHANNEL = 'catsnap:info'

# This code listens for messages published to redis and sends them along
# to websockets. It handles the grody gevent logic so individual socket/redis
# connecting endpoints can focus on "what messages do I care about?"
class RedisWebsocketBridge(Singleton):
    def __init__(self):
        self.clients = []
        self.pubsub = redis.pubsub()
        self.start()

    def __iter_data(self):
        for message in self.pubsub.listen():
            data = message.get('data')
            if message['type'] == 'message':
                try:
                    data = json.loads(data)
                except TypeError, ValueError:
                    pass
                yield data

    # This is the main function that other code will use. It takes three args:
    # * client is a websocket client of the sort passed into functions
    #   decorated with @socket.route
    # * relevant is a function that receives a published message and returns a
    #   boolean indicating whether that method is relevant to the client.
    # * translate is a function that receives a published message and returns
    #   a string to be sent to the websocket client.
    def register(self, client, relevant, translate):
        self.clients.append((client, relevant, translate))

    def send(self, client, data):
        if type(data) not in [str, unicode]:
            data = json.dumps(data)
        try:
            client.send(data)
        except WebSocketError:
            self.clients.remove(client)

    def run(self):
        self.pubsub.subscribe(REDIS_CHANNEL)
        for data in self.__iter_data():
            for client, relevant, translate in self.clients:
                if relevant(data):
                    gevent.spawn(self.send, client, translate(data))

    def start(self):
        gevent.spawn(self.run)
