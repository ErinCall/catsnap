from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String
from sqlalchemy.sql.functions import coalesce
from catsnap import Client
from catsnap.table.created_at_bookkeeper import CreatedAtBookkeeper

class Album(CreatedAtBookkeeper):
    __tablename__ = 'album'

    album_id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)

    @classmethod
    def images_for_album_id(cls, album_id):
        from catsnap.table.image import Image
        session = Client().session()
        return session.query(Image).\
                filter(Image.album_id == album_id).\
                order_by(coalesce(Image.photographed_at, Image.created_at)).\
                all()
