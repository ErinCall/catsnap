#! /bin/bash

set -e

source Env/bin/activate
gunicorn catsnap.app:app -b 0.0.0.0:5000 -w 3
