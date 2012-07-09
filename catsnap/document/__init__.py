from __future__ import unicode_literals

from catsnap import Config

class Document():
    _stored_table = None

    def _table(self):
        self._stored_table = self._stored_table \
                or Config().table(self._table_name)
        return self._stored_table

