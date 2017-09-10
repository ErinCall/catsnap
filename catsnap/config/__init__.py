

import os
import yaml
from catsnap.singleton import Singleton
from functools import reduce

# main configuration for catsnap. Looks for settings in os.environ or
# config.yml (env vars first). Acts like a read-only dict; use [] to look up
# settings. Raises an AttributeError (*not* a KeyError) if given a key that
# isn't even a real setting name.

class Config(Singleton):
    ALL_SETTINGS = [
        'postgres_url',
        'extension',
        'redis_url',
        'aws.access_key_id',
        'aws.secret_access_key',
        'aws.bucket',
        'aws.cloudfront_distribution_id',
        'secret_session_key',
        'password_hash',
        'error_email.provider.hostname',
        'error_email.provider.username',
        'error_email.provider.password',
        'error_email.recipient',
        'error_email.sender',
        'twitter_username',
    ]
    _contents = None

    def __getitem__(self, item):
        if item not in self.ALL_SETTINGS:
            raise AttributeError(item)
        try:
            return os.environ[self.environ_name(item)]
        except KeyError:
            # this reduce call uses dot-separated setting names as a path for
            # looking up items in a nested dictionary. So, for example,
            # error_email.provider.username becomes
            # self._file()[error_email][provider][username]
            return reduce(lambda conf, key: conf[key],
                          item.split('.'),
                          self._file())

    def __contains__(self, item):
        try:
            self[item]
            return True
        except KeyError:
            return False

    def _file(self):
        if self._contents is None:
            config_file_name = os.path.join(
                    os.path.dirname(__file__), 'config.yml')
            if os.path.exists(config_file_name):
                with open(config_file_name, 'r') as fh:
                    self._contents = yaml.load(fh.read())
            else:
                self._contents = {}

        return self._contents

    def environ_name(self, item):
        return 'CATSNAP_' + item.upper().replace('.', '_')
