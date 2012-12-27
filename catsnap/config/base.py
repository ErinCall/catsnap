from __future__ import unicode_literals

class Config(object):
    CREDENTIAL_SETTINGS = ('aws_access_key_id', 'aws_secret_access_key')
    ALL_SETTINGS = CREDENTIAL_SETTINGS + ('bucket',
                                          'extension',
                                          'owner_id',
                                          'api_host',
                                          'api_key')
    CLIENT_SETTINGS = ('extension', 'api_host', 'api_key')

    def __getitem__(self, item): raise NotImplementedError
    def __contains__(self, item): raise NotImplementedError
