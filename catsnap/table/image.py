from __future__ import unicode_literals

from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    select,
    alias,
    func,
    or_,
    ForeignKey,
    LargeBinary,
)
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from catsnap import Client
from catsnap.table.album import Album
from catsnap.table.created_at_bookkeeper import CreatedAtBookkeeper


class Image(CreatedAtBookkeeper):
    __tablename__ = 'image'

    image_id = Column(Integer, primary_key=True)
    album_id = Column(Integer, ForeignKey(Album.album_id))
    filename = Column(String)
    source_url = Column(String)
    title = Column(String)
    description = Column(String)
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
# SELECT
#     image.*
# FROM (
#     select max(image.image_id) as image_id
#     from image
#     where image.album_id = 1 and image.image_id < 1614
#     union all
#     select min(image.image_id) as image_id
#     from image
#     where image.album_id = 1 and image.image_id > 1614
# ) as neighbors
# left outer join image using (image_id)
# ;
        session = Client().session()
        neighbors_query = alias(select([
                func.max(Image.image_id).label('image_id')]).
            where(Image.album_id == self.album_id).
            where(Image.image_id < self.image_id).
            union(select([func.min(Image.image_id)]).
                where(Image.album_id == self.album_id).
                where(Image.image_id > self.image_id)),
            'neighbors')

        # query = session.query(image_query).\
        #     select_from(neighbors_query).\
        #     outerjoin(Image, Image.image_id == neighbors_query.c.image_id)

        column_names = [c.name for c in Image.__table__.columns]
        query = select(['image.{0}'.format(c) for c in column_names]).\
            select_from(neighbors_query.\
            outerjoin(Image, Image.image_id == neighbors_query.c.image_id))

        records = session.execute(query).fetchall()
        print records

        neighbors = map(lambda r: Image(**dict(zip(column_names, r.values()))) if any(r) else None, records)
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

    def __repr__(self):
        return "<Image filename={0}>".format(self.filename)

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

    def __new__(cls, *args, **kwargs):
        try:
            image_id = kwargs['image_id']
            width = kwargs['width']
            height = kwargs['height']
        except KeyError:
            return super(ImageResize, cls).__new__(cls, *args, **kwargs)

        session = Client().session()
        existing_resize = session.query(cls).\
            filter(cls.image_id == image_id).\
            filter(cls.width == width).\
            filter(cls.height == height).\
            first()

        if existing_resize:
            return existing_resize

        return super(ImageResize, cls).__new__(cls, *args, **kwargs)

class ImageContents(CreatedAtBookkeeper):
    __tablename__ = 'image_contents'

    image_contents_id = Column(Integer, primary_key=True)
    image_id = Column(Integer, ForeignKey(Image.image_id), nullable=False)
    contents = Column(LargeBinary, nullable=False)
    content_type = Column(String, nullable=False)
