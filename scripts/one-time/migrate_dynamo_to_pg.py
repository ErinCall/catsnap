#!/usr/bin/env python

import json
from sqlalchemy import Table, Column, String, MetaData
from catsnap import Client
from catsnap.table.tag import Tag
from catsnap.table.image import Image
from catsnap.table.image_tag import ImageTag

tags = []
images = []
image_tags = []

tag_table = Client().table('tag')
for item in tag_table.scan():
    tags.append({
        'name': item['tag']})

image_table = Client().table('image')
for item in image_table.scan():
    images.append({
        'filename': item['tag'],
        'source_url': item.get('source_url', '')})
    for tag in json.loads(item['tags']):
        image_tags.append({
            'filename': item['tag'],
            'tag_name': tag})

session = Client().session()
metadata = MetaData(bind=Client()._engine)

temp_image_tag = Table(
        'temp_image_tags',
        metadata,
        Column('tag_name', String, primary_key=True),
        Column('filename', String, primary_key=True),
        prefixes=['temporary'],
        )
metadata.create_all()

session.execute(temp_image_tag.insert(image_tags))
session.execute(Image.__table__.insert(images))
session.execute(Tag.__table__.insert(tags))

#I can't figure out how to make sqlalchemy generate this query! :(
session.execute("""
insert into image_tag (image_id, tag_id) (
select
    image.image_id,
    tag.tag_id
from
    temp_image_tags
    inner join image using (filename)
    inner join tag on tag.name = temp_image_tags.tag_name
)
        """)

session.commit()
