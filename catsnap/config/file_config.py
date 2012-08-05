from __future__ import unicode_literals

import ConfigParser
import os
import sys
import getpass

LEGACY_CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
CREDENTIAL_SETTINGS = ('aws_access_key_id', 'aws_secret_access_key')
ALL_SETTINGS = CREDENTIAL_SETTINGS + ('bucket', )
CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')
BUCKET_BASE = 'catsnap'

class FileConfig(object):
    def __init__(self):
        self._parser = ConfigParser.ConfigParser()
        self._parser.read(LEGACY_CREDENTIALS_FILE)
        self._parser.read(CONFIG_FILE)

    def __getitem__(self, item):
        section = 'catsnap'
        if item in CREDENTIAL_SETTINGS:
            section = 'Credentials'
        return self._parser.get(section, item)

    def __contains__(self, item):
        section = 'catsnap'
        if item in CREDENTIAL_SETTINGS:
            section = 'Credentials'
        return self._parser.has_option(section, item)

    def collect_settings(self, settings_to_get=None):
        if not settings_to_get:
            settings_to_get = ALL_SETTINGS

        sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                         "gp/aws/securityCredentials\n")

        if 'aws_access_key_id' in settings_to_get:
            self._get_setting('Credentials', 'aws_access_key_id',
                    'Enter your access key id%s: ',
                    " (leave blank to keep using '%s')",
                    self._input)
        if 'aws_secret_access_key' in settings_to_get:
            self._get_setting('Credentials', 'aws_secret_access_key',
                    'Enter your secret access key%s: ',
                    " (leave blank to keep using what you had before)",
                    getpass.getpass)
        if 'bucket' in settings_to_get:
            self._get_setting('catsnap', 'bucket',
                    "Please name your bucket%s: ",
                    " (leave blank to use '%s')",
                    self._input,
                    global_default='%s-%s' % (BUCKET_BASE, os.environ['USER']))
        with open(CONFIG_FILE, 'w') as config_file:
            self._parser.write(config_file)

    def _get_setting(self, section, setting_name, message,
                    override_message, read,
                    global_default=None):
        if not self._parser.has_section(section):
            self._parser.add_section(section)

        has_setting = self._parser.has_option(section, setting_name)
        use_default = ''
        if global_default:
            use_default = override_message % global_default
        if has_setting:
            try:
                use_default = override_message % \
                        self._parser.get(section, setting_name)
            except TypeError:
                use_default = override_message
        setting_value = read(message % use_default)
        if has_setting and not setting_value:
            setting_value = self._parser.get(section, setting_name)
        setting_value = setting_value or global_default
        self._parser.set(section, setting_name, setting_value)

    def _input(self, *args, **kwargs):
        return raw_input(*args, **kwargs)

