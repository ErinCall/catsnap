from __future__ import unicode_literals

import time
from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    func,
    or_,
    ForeignKey,
)
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
    created_at = Column(DateTime)
    photographed_at = Column(DateTime)
    aperture = Column(String)
    shutter_speed = Column(String)
    iso = Column(Integer)
    focal_length = Column(Integer)
    camera = Column(String)

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

    def __init__(self, *args, **kwargs):
        super(Image, self).__init__(*args, **kwargs)
        self.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())

    @classmethod
    def find_by_filename(cls, filename):
        session = Client().session()
        images = session.query(cls).filter(
            func.upper(cls.filename) == func.upper(filename))
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

        existing_image_tags = session.query(ImageTag.tag_id).\
            filter(ImageTag.image_id == self.image_id).\
            filter(ImageTag.tag_id.in_([t.tag_id for t in tags])).\
            all()
        existing_image_tags = [row[0] for row in existing_image_tags]

        for tag in tags:
            if tag.tag_id in existing_image_tags:
                continue
            session.add(ImageTag(tag_id=tag.tag_id, image_id=self.image_id))

    def remove_tag(self, tag_name):
        from catsnap.table.image_tag import ImageTag
        from catsnap.table.tag import Tag
        session = Client().session()
        image_tag = session.query(ImageTag).\
                join(Tag, Tag.tag_id == ImageTag.tag_id).\
                filter(Tag.name == tag_name).\
                filter(ImageTag.image_id == self.image_id).\
                one()
        session.delete(image_tag)

    def neighbors(self):
        if self.album_id is None:
            return (None, None)
        else:
            session = Client().session()
            neighbors = session.query(Image).\
                filter(Image.album_id == self.album_id).\
                filter(or_(
                    Image.image_id == session.query(func.max(Image.image_id)).
                        filter(Image.image_id < self.image_id),
                    Image.image_id == session.query(func.min(Image.image_id)).
                        filter(Image.image_id > self.image_id))).\
                order_by(Image.created_at).\
                all()
            if len(neighbors) == 2:
                return (neighbors[0], neighbors[1])
            elif len(neighbors) == 1 and neighbors[0].image_id > self.image_id:
                return (None, neighbors[0])
            elif len(neighbors) == 1 and neighbors[0].image_id < self.image_id:
                return (neighbors[0], None)
            else:
                return (None, None)

    def caption(self):
        get_tags = lambda: list(self.get_tags())
        return self.make_caption(title=self.title,
                get_tags=get_tags,
                filename=self.filename)

    @classmethod
    def make_caption(cls, filename, title, get_tags):
        if title:
            return title
        tags = get_tags()
        if tags:
            return ' '.join(tags)
        return filename


class ImageResize(Base):
    __tablename__ = 'image_resize'

    image_id = Column(Integer, ForeignKey(Image.image_id), primary_key=True)
    width = Column(Integer, primary_key=True)
    height = Column(Integer, primary_key=True)
    suffix = Column(String, nullable=False)
