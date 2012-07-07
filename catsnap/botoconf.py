from __future__ import unicode_literals
import os
import sys
import getpass

CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')

def ensure_aws_credentials_exist():
    if os.path.exists(CREDENTIALS_FILE):
        return
    credentials = get_aws_credentials()
    with open(CREDENTIALS_FILE, 'w', 0600) as creds_file:
        creds_file.write(credentials)

def get_aws_credentials():
    sys.stdout.write("Looks like this is your first run.\n")
    sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                     "gp/aws/securityCredentials\n")
    key_id = getpass.getpass('Enter your access key id: ')
    key = getpass.getpass('Enter your secret access key: ')
    return """[Credentials]
aws_access_key_id = %(key_id)s
aws_secret_access_key = %(key)s""" % {'key_id': key_id, 'key': key}
