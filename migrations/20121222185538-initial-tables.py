step(
        """
create table image (
    image_id serial primary key,
    filename text not null,
    source_url text
)
        """,
        """
drop table image
        """
)
step(
        """
create unique index unq_image_filename
    on image (filename)
        """
)

step(
        """
create table tag (
    tag_id serial primary key,
    name text not null
)
        """,
        """
drop table tag
        """,
)
step(
        """
create unique index unq_tag_name
    on tag (name)
        """,
)

step(
        """
create table image_tag (
    tag_id integer not null references tag (tag_id),
    image_id integer not null references image (image_id)
)
        """,
        """
drop table image_tag
        """
)
