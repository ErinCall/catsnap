step(
        """
        create table image_resize (
            image_id integer references image (image_id),
            width integer,
            height integer,
            suffix text not null,
            constraint image_resize_pk
                primary key (image_id, width, height)
        )
        """,
        """
        drop table image_resize
        """
)
