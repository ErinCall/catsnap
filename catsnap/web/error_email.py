from __future__ import unicode_literals

import os
from logging.handlers import SMTPHandler


class ErrorEmail(object):
    def init_app(self, app):
        if app.debug or not all(map(lambda x: x in os.environ,
                                     ['EMAIL_HOST',
                                     'ERROR_RECIPIENT',
                                     'ERROR_SENDER'])):
            return

        if 'EMAIL_USERNAME' in os.environ and 'EMAIL_PASSWORD' in os.environ:
            email_credentials = (os.environ['EMAIL_USERNAME'],
                                 os.environ['EMAIL_PASSWORD'])
        else:
            email_credentials = None
        mail_handler = SMTPHandler(os.environ['EMAIL_HOST'],
                                   os.environ['ERROR_SENDER'],
                                   [os.environ['ERROR_RECIPIENT']],
                                   'Catsnap error',
                                   email_credentials)
        mail_handler.setLevel(logging.ERROR)
        mail_handler.setFormatter(logging.Formatter('''
Message type:       %(levelname)s
Location:           %(pathname)s:%(lineno)d
Module:             %(module)s
Function:           %(funcName)s
Time:               %(asctime)s

Message:

%(message)s
'''))
        app.logger.addHandler(mail_handler)
