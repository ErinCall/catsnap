from __future__ import unicode_literals

import ConfigParser
import os
import sys
import getpass

from catsnap.config.base import Config

LEGACY_CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')
BUCKET_BASE = 'catsnap'

def _input(*args, **kwargs):
    return raw_input(*args, **kwargs)


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

    def collect_settings(self, settings_to_get=None):
        if not settings_to_get:
            settings_to_get = self.ALL_SETTINGS

        sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                         "gp/aws/securityCredentials\n")

        for setting in settings_to_get:
            self._get_setting(setting)

        with open(CONFIG_FILE, 'w') as config_file:
            self._parser.write(config_file)

    def _get_setting(self, setting_name):
        setting = self.setting_definitions[setting_name]

        if not self._parser.has_section(setting.section):
            self._parser.add_section(setting.section)

        has_setting = self._parser.has_option(setting.section, setting.name)
        use_default = ''
        if setting.global_default:
            use_default = setting.override_message % setting.global_default
        if has_setting:
            try:
                use_default = setting.override_message % \
                        self._parser.get(setting.section, setting.name)
            except TypeError:
                use_default = setting.override_message
        setting_value = setting.read_method(setting.message % use_default)
        if has_setting and not setting_value:
            setting_value = self._parser.get(setting.section, setting.name)
        setting_value = setting_value or setting.global_default
        self._parser.set(setting.section, setting.name, setting_value)

    @classmethod
    def _setting_definitions(cls):
        return {setting.name: setting for setting in (
            FileSetting(
                section='Credentials',
                name='aws_access_key_id',
                message='Enter your access key id%s: ',
                override_message=" (leave blank to keep using '%s')"),
            FileSetting(
                section='Credentials',
                name='aws_secret_access_key',
                message='Enter your secret access key%s: ',
                override_message=" (leave blank to keep using "
                                 "what you had before)",
                read_method=getpass.getpass),
            FileSetting(
                section='catsnap',
                name='bucket',
                message="Please name your bucket%s: ",
                global_default='%s-%s' % (BUCKET_BASE, os.environ['USER']),
                override_message=" (leave blank to use '%s')"),
            FileSetting(
                section='catsnap',
                name='extension',
                message='Would you like to print a fake file extension '
                        'on urls%s? ',
                override_message="(leave blank to keep using '%s')",
                parser_getter='getboolean'),
        )}


class FileSetting(object):
    section = NotImplemented
    name = NotImplemented
    message = NotImplemented
    override_message = NotImplemented
    read_method = None
    global_default = None
    parser_getter = 'get'

    def __init__(self, **kwargs):
        for attr, value in kwargs.iteritems():
            if hasattr(self, attr):
                setattr(self, attr, value)
            else:
                raise TypeError(attr)
        if 'read_method' not in kwargs:
            self.read_method = _input

        for attr in dir(self):
            if getattr(self, attr) is NotImplemented:
                raise NotImplementedError(attr)

