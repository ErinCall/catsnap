from __future__ import unicode_literals

class Config(object):
    CREDENTIAL_SETTINGS = ('aws_access_key_id', 'aws_secret_access_key')
    ALL_SETTINGS = CREDENTIAL_SETTINGS + ('bucket',
                                          'extension',
                                          'password_hash',
                                          'twitter_username',
                                          'redis_url',
                                          'cloudfront_distribution_id')

    def __getitem__(self, item): raise NotImplementedError
    def __contains__(self, item): raise NotImplementedError
