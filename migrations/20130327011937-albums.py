step(
        """
        create table album (
            album_id serial primary key,
            name text not null,
            created_at timestamp not null
        )
        """,
        """
        drop table album
        """
)

step(
        """
        alter table image
        add column album_id integer references album (album_id)
        """,
        """
        alter table image
        drop column album_id
        """
)
