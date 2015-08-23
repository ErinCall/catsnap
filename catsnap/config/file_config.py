from __future__ import unicode_literals

import ConfigParser
import os
import sys
import getpass

from catsnap.config.base import Config

LEGACY_CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')
BUCKET_BASE = 'catsnap'


class FileConfig(Config):
    def __init__(self):
        self._parser = ConfigParser.ConfigParser()
        self._parser.read(LEGACY_CREDENTIALS_FILE)
        self._parser.read(CONFIG_FILE)
        self.setting_definitions = self._setting_definitions()

        for setting in self.ALL_SETTINGS:
            if setting not in self.setting_definitions:
                raise AttributeError(setting)

    def __getitem__(self, item):
        section = 'catsnap'
        if item in self.CREDENTIAL_SETTINGS:
            section = 'Credentials'

        getter = getattr(self._parser,
                self.setting_definitions[item].parser_getter)
        return getter(section, item)

    def __contains__(self, item):
        section = 'catsnap'
        if item in self.CREDENTIAL_SETTINGS:
            section = 'Credentials'
        return self._parser.has_option(section, item)

    @classmethod
    def _setting_definitions(cls):
        return {setting.name: setting for setting in (
            FileSetting(
                section='Credentials',
                name='aws_access_key_id',
                ),
            FileSetting(
                section='Credentials',
                name='aws_secret_access_key',
                ),
            FileSetting(
                section='catsnap',
                name='bucket',
                ),
            FileSetting(
                section='catsnap',
                name='extension',
                parser_getter='getboolean'),
            FileSetting(
                section='catsnap',
                name='password_hash',
                ),
            FileSetting(
                section='catsnap',
                name='twitter_username',
                ),
            FileSetting(
                section='catsnap',
                name='cloudfront_distribution_id',
                ),
            FileSetting(
                section='catsnap',
                name='redis_url',
                ),
        )}


class FileSetting(object):
    section = NotImplemented
    name = NotImplemented
    parser_getter = 'get'

    def __init__(self, **kwargs):
        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)
            else:
                raise TypeError(attr)

        for attr in dir(self):
            if getattr(self, attr) is NotImplemented:
                raise NotImplementedError(attr)

