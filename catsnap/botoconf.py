from __future__ import unicode_literals
import os
import sys
import getpass
import boto

from catsnap import settings

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

def connect():
    s3 = boto.connect_s3()
    all_buckets = [x.name for x in s3.get_all_buckets()]
    if settings.BUCKET not in all_buckets:
        bucket = s3.create_bucket(settings.BUCKET)
    else:
        bucket = s3.get_bucket(settings.BUCKET)
    return bucket
