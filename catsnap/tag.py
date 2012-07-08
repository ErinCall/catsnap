from __future__ import unicode_literals

class Tag():
    def __init__(self, name):
        self.name = name

    def save(self, table, filename):
        item = table.new_item(hash_key=self.name, attrs={filename: filename})
        item.put()
