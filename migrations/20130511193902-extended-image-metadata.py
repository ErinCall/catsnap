step(
        """
        alter table image
            add column created_at timestamp without time zone,
            add column photographed_at timestamp without time zone,
            add column aperture text,
            add column shutter_speed text,
            add column focal_length integer,
            add column camera text,
            add column iso integer
        """,
        """
        alter table image
            drop column created_at,
            drop column photographed_at,
            drop column aperture,
            drop column shutter_speed,
            drop column focal_length,
            drop column camera,
            drop column iso
        """
)
