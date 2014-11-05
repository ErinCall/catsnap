step(
        """
        create unique index unq_album_name on album (name)
        """,
        """
        drop index unq_album_name
        """
)
