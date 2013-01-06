from __future__ import unicode_literals

from catsnap.singleton import Singleton
from catsnap.config.base import Config
from catsnap.config.argument_config import ArgumentConfig
from catsnap.config.env_config import EnvConfig
from catsnap.config.file_config import FileConfig

class MetaConfig(object):
    _file_config = {}
    _env_config = {}
    _argument_config = {}
    _defaults = {'extension': False}

    def __init__(self, include_arg_config=False):
        self._file_config = FileConfig()
        self._env_config = EnvConfig()
        if include_arg_config:
            self._argument_config = ArgumentConfig()

    def __getitem__(self, item):
        for subconfig in (self._argument_config,
                          self._file_config,
                          self._env_config,
                          self._defaults):
            if item in subconfig:
                return subconfig[item]

        raise KeyError("Couldn't find any setting at all for '%s'. You'll need "
                "to supply it in some way--try `catsnap config`, or see the "
                "docs for other ways to supply a setting." % item)

    def __contains__(self, item):
        return any(map(lambda x: item in x, [self._argument_config,
                                             self._file_config,
                                             self._env_config,
                                             self._defaults]))

    def __getattr__(self, item):
        if item not in Config.ALL_SETTINGS:
            raise AttributeError(item)
        return self[item]
