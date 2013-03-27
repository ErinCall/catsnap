from __future__ import unicode_literals

import time
from sqlalchemy import Column, Integer, String, DateTime
from catsnap import Client
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Album(Base):
    __tablename__ = 'album'

    album_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, nullable=False)

    def __init__(self, *args, **kwargs):
        super(Album, self).__init__(*args, **kwargs)
        self.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

    def images(self):
        from catsnap.table.image import Image
        session = Client().session()
        return session.query(Image).\
                filter(Image.album_id == self.album_id).\
                all()
