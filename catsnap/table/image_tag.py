from __future__ import unicode_literals

from sqlalchemy import Column, Integer, ForeignKey
from catsnap.table.tag import Tag
from catsnap.table.image import Image
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class ImageTag(Base):
    __tablename__ = 'image_tag'

    image_id = Column(Integer, ForeignKey(Image.image_id), primary_key=True)
    tag_id = Column(Integer, ForeignKey(Tag.tag_id), primary_key=True)
