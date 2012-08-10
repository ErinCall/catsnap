from __future__ import unicode_literals
import os

from catsnap.config.base import Config

class EnvConfig(Config):
    def __getitem__(self, item):
        env_var = 'CATSNAP_' + item.upper()
        return os.environ[env_var]

    def __contains__(self, item):
        env_var = 'CATSNAP_' + item.upper()
        return env_var in os.environ
