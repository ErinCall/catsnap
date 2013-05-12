step(
        """
        alter table image
            add column title text,
            add column description text
        """,
        """
        alter table image
            drop column description,
            drop column title
        """
)
