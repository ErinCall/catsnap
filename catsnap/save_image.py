import hashlib

def save_image(bucket, contents, content_type):
    key = bucket.new_key(key_for_image(contents))
    key.set_metadata('Content-Type', content_type)
    key.set_contents_from_string(contents)
    key.make_public()

def key_for_image(contents):
    return hashlib.sha1(contents).hexdigest()
