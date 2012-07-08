from __future__ import unicode_literals
import os
import sys
import getpass
import boto

from catsnap import settings

CREDENTIALS_FILE = os.path.join(os.environ['HOME'], '.boto')
CONFIG_FILE = os.path.join(os.environ['HOME'], '.catsnap')

def ensure_config_files_exist():
    if not all(map(os.path.exists, [ CONFIG_FILE, CREDENTIALS_FILE ])):
        sys.stdout.write("Looks like this is your first run.\n")
        if not os.path.exists(CONFIG_FILE):
            config = get_catsnap_config()
            with open(CONFIG_FILE, 'w', 0600) as config_file:
                config_file.write(config)
        if not os.path.exists(CREDENTIALS_FILE):
            credentials = get_aws_credentials()
            with open(CREDENTIALS_FILE, 'w', 0600) as creds_file:
                creds_file.write(credentials)
    else:
        return

def get_aws_credentials():
    sys.stdout.write("Find your credentials at https://portal.aws.amazon.com/"
                     "gp/aws/securityCredentials\n")
    key_id = getpass.getpass('Enter your access key id: ')
    key = getpass.getpass('Enter your secret access key: ')
    return """[Credentials]
aws_access_key_id = %(key_id)s
aws_secret_access_key = %(key)s""" % {'key_id': key_id, 'key': key}

def get_catsnap_config():
    bucket_name = '%s-%s' % (settings.BUCKET_BASE, os.environ['USER'])
    actual_bucket_name = _input("Please name your bucket (leave blank to use "
            "'%s'): " % bucket_name)
    bucket_name = actual_bucket_name or bucket_name
    return """[catsnap]
bucket = %s""" % bucket_name


def connect():
    s3 = boto.connect_s3()
    all_buckets = [x.name for x in s3.get_all_buckets()]
    if settings.BUCKET_BASE not in all_buckets:
        bucket = s3.create_bucket(settings.BUCKET_BASE)
    else:
        bucket = s3.get_bucket(settings.BUCKET_BASE)
    return bucket

def _input(*args, **kwargs):
    return raw_input(*args, **kwargs)
