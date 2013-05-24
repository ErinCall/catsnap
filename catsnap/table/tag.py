from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, func
from catsnap import Client
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()

class Tag(Base):
    __tablename__ = 'tag'

    tag_id = Column(Integer, primary_key=True)
    name = Column(String)

    def get_filenames(self):
        from catsnap.table.image import Image
        from catsnap.table.image_tag import ImageTag
        session = Client().session()
        filenames = session.query(Image.filename).\
                join(ImageTag).\
                filter(ImageTag.image_id == Image.image_id).\
                filter(ImageTag.tag_id == self.tag_id)
        for filename in filenames:
            yield filename[0]

    @classmethod
    def get_image_data(cls, tag_names):
        from catsnap.table.image import Image
        from catsnap.table.image_tag import ImageTag
        session = Client().session()
        image_data = session.query(func.max(Image.filename),
                                   Image.image_id,
                                   func.max(Image.title),
                                   func.array_agg(Tag.name)).\
                join(ImageTag).\
                filter(ImageTag.image_id == Image.image_id).\
                filter(ImageTag.tag_id == Tag.tag_id).\
                filter(Image.image_id.in_(
                    session.query(ImageTag.image_id).\
                            join(Tag).\
                            filter(ImageTag.tag_id == Tag.tag_id).\
                            filter(Tag.name.in_(tag_names)))).\
                group_by(Image.image_id).\
                order_by(Image.filename)

        for image_struct in image_data:
            caption = Image.make_caption(title=image_struct[2],
                filename=image_struct[0],
                tags=image_struct[3])
            yield (image_struct[0], image_struct[1], caption)
