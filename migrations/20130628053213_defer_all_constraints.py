step(
	"""
		alter table image
			drop constraint image_album_id_fkey,
			add constraint image_album_id_fkey 
				foreign key (album_id) references album (album_id) deferrable
	""",
	"""
		alter table image
			drop constraint image_album_id_fkey,
			add constraint image_album_id_fkey
				foreign key (album_id) references album (album_id)
	"""
)
step(
	"""
		alter table image_resize
			drop constraint image_resize_image_id_fkey,
			add constraint image_resize_image_id_fkey
				foreign key (image_id) references image (image_id) deferrable
	""",
	"""
		alter table image_resize
			drop constraint image_resize_image_id_fkey,
			add constraint image_resize_image_id_fkey
				foreign key (image_id) references image (image_id)
	"""
)
step(
	"""
		alter table image_tag
			drop constraint image_tag_image_id_fkey,
			drop constraint image_tag_tag_id_fkey,
			add constraint image_tag_image_id_fkey
				foreign key (image_id) references image (image_id) deferrable,
			add constraint image_tag_tag_id_fkey
				foreign key (tag_id) references tag (tag_id) deferrable
	""",
	"""
		alter table image_tag
			drop constraint image_tag_image_id_fkey,
			drop constraint image_tag_tag_id_fkey,
			add constraint image_tag_image_id_fkey
				foreign key (image_id) references image (image_id),
			add constraint image_tag_tag_id_fkey
				foreign key (tag_id) references tag (tag_id)
	"""
)