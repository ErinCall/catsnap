from __future__ import unicode_literals

from sqlalchemy import Column, Integer, String, func, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from catsnap import Client
from catsnap.table.album import Album

class Image(Base):
    __tablename__ = 'image'

    image_id = Column(Integer, primary_key=True)
    album_id = Column(Integer, ForeignKey(Album.album_id))
    filename = Column(String)
    source_url = Column(String)
    title = Column(String)
    description = Column(String)

    def __new__(cls, *args, **kwargs):
        filename = None
        if args:
            filename = args[0]
        if not filename:
            filename = kwargs.get('filename')
        if filename:
            session = Client().session()
            existing_image = session.query(cls).\
                    filter(cls.filename == filename).\
                    first()

            if existing_image:
                return existing_image

        return super(Image, cls).__new__(cls, *args, **kwargs)

    @classmethod
    def find_by_filename(cls, filename):
        session = Client().session()
        images = session.query(cls).filter(func.upper(cls.filename)
                                          == func.upper(filename))
        return images.first()

    def get_tags(self):
        #whee circular references
        from catsnap.table.image_tag import ImageTag
        from catsnap.table.tag import Tag
        session = Client().session()
        tags = session.query(Tag.name).\
                join(ImageTag).\
                filter(ImageTag.image_id == self.image_id).\
                filter(ImageTag.tag_id == Tag.tag_id)
        for row in tags:
            yield row[0]

    def add_tags(self, tag_names):
        from catsnap.table.image_tag import ImageTag
        from catsnap.table.tag import Tag
        session = Client().session()
        tags = session.query(Tag).\
                filter(Tag.name.in_(tag_names)).\
                all()
        new_tags = set(tag_names) - set([t.name for t in tags])
        for tag_name in new_tags:
            tag = Tag(name=tag_name)
            session.add(tag)
            tags.append(tag)
        session.flush()

        for tag in tags:
            session.add(ImageTag(tag_id=tag.tag_id, image_id=self.image_id))
