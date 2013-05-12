import os
import sys
import traceback
import smtplib
from email.mime.text import MIMEText

class ExceptionNotifier(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except Exception:
            (exc_type, exc_value, trace) = sys.exc_info()
            formatted_trace = traceback.format_exception(exc_type,
                                                         exc_value,
                                                         trace)

            body = 'An exception was raised in catsnap\n'
            body += "\n".join(formatted_trace)
            body += 'Request env:'
            for key, value in environ.iteritems():
                body += "'%s' = '%s'\n" % (key, value)

            message = MIMEText(body)
            message['Subject'] = 'Catsnap Exception'
            message['From'] = os.environ['CATSNAP_EXCEPTION_ADDRESS']
            message['To'] = os.environ['CATSNAP_EXCEPTION_ADDRESS']

            try:
                smtp = smtplib.SMTP('smtp.sendgrid.net', 25)
                smtp.login(os.environ['SENDGRID_USERNAME'],
                           os.environ['SENDGRID_PASSWORD'])
                smtp.sendmail(message['From'],
                             [message['To']],
                             message.as_string())
                smtp.quit()
            except Exception as e:
                print "###################################"
                print "AND I couldn't email the exception:"
                print e
                print "###################################"

            raise exc_type, exc_value, trace
