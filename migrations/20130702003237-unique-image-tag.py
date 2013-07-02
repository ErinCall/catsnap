step(
    """
        create unique index unq_image_tag_image_id_tag_id
            on image_tag (image_id, tag_id)
    """,
    """
        drop index unq_image_tag_image_id_tag_id
    """
)
