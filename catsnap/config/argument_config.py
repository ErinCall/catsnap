from __future__ import unicode_literals

import sys
import argparse

from catsnap.config.base import Config

class ArgumentConfig(Config):
    def __init__(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--aws-access-key-id', help="Your AWS access key "
                "id (Find your credentials at https://portal.aws.amazon.com/"
                "gp/aws/securityCredentials)")
        parser.add_argument('--aws-secret-access-key', help="Your AWS secret "
                "access key (Find your credentials at https://portal.aws."
                "amazon.com/gp/aws/securityCredentials)")
        parser.add_argument('--bucket', help="The S3 bucket you want catsnap "
                "to use")
        parser.add_argument('-e', '--extension', action='store_true',
                default=None,
                help="Append #.gif to urls (i.e. for pasting in Campfire)")
        parser.add_argument('--no-extension', action='store_false',
                dest='extension', default=None,
                help="Do no append #.gif to urls")
        parser.add_argument('arg', nargs='*')

        #We're manually grabbing sys.argv so the tests can easily mock it
        #We need to drop the first item because argparse will see it as an
        #argument, rather than as the script-name
        argv = sys.argv[1:]
        self._args = parser.parse_args(argv)

        for setting in self.ALL_SETTINGS:
            if not hasattr(self._args, setting):
                raise AttributeError(setting)

    def __getitem__(self, item):
        try:
            argument = getattr(self._args, item)
            if argument is None:
                raise KeyError(item)
            return argument
        except AttributeError:
            raise KeyError(item)

    def __contains__(self, item):
        return hasattr(self._args, item) and \
                getattr(self._args, item) is not None
