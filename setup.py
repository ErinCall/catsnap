#!/usr/bin/python

from setuptools import setup

setup(name="catsnap",
      version="6.0.0",
      description="catalog and store images",
      author="Erin Call",
      author_email="hello@erincall.com",
      url="https://github.com/ErinCall/",
      packages=['catsnap',
                'catsnap.document',
                'catsnap.config',
                'catsnap.batch'],
      install_requires=[
          "Flask==0.9",
          "gunicorn==0.14.6",
          "boto==2.40.0",
          "requests==2.21.0",
          "argparse==1.2.1",
          "psycopg2-binary==2.7.7",
          "sqlalchemy==0.8.0b2",
          "yoyo-migrations==6.0.0",
          "wand==0.3.3",
          "celery==3.1.16",
          "redis==2.10.3",
          "gevent==1.1b5",
          "Flask-Sockets==0.1",
          "PyYAML==3.11",

          "mock==1.0.1",
          "nose==1.1.2",
          "selenium==3.141.0",
          "splinter==0.10.0",
          "bcrypt==1.1.1",
      ],
      )
