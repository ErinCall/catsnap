from __future__ import unicode_literals, absolute_import

import gevent
import json
import redis as redislib
from catsnap import Client
from catsnap.singleton import Singleton
from geventwebsocket.exceptions import WebSocketError

redis = redislib.from_url(Client().config().redis_url)
REDIS_CHANNEL = 'catsnap:info'

class RedisWebsocketBridge(Singleton):
    def __init__(self):
        self.clients = []
        self.pubsub = redis.pubsub()
        self.pubsub.subscribe(REDIS_CHANNEL)
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

    def register(self, client):
        self.clients.append(client)

    def send(self, client, data):
        if type(data) not in [str, unicode]:
            data = json.dumps(data)
        try:
            client.send(data)
        except WebSocketError:
            self.clients.remove(client)

    def run(self):
        for data in self.__iter_data():
            for client, relevant, translate in self.clients:
                if relevant(data):
                    gevent.spawn(self.send, client, translate(data))

    def start(self):
        gevent.spawn(self.run)
