step(
        """
        create table image_contents (
            image_contents_id serial primary key,
            image_id integer references image (image_id) not null,
            created_at timestamp without time zone not null,
            contents bytea not null,
            content_type character varying (10) not null,
            constraint image_contents_content_type_domain
                check (content_type in (
                    'image/jpeg',
                    'image/png',
                    'image/gif')
                )
        )
        """,
        """
        drop table image_contents
        """
)
