from __future__ import unicode_literals

import requests

def load_image(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.content
