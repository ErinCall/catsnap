from __future__ import unicode_literals
import os

class EnvConfig(object):
    def __getitem__(self, item):
        env_var = 'CATSNAP_' + item.upper()
        return os.environ[env_var]

    def __contains__(self, item):
        env_var = 'CATSNAP_' + item.upper()
        return env_var in os.environ
