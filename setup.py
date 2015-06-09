#!/usr/bin/python

from setuptools import setup

setup(name="catsnap",
      version="5.2.3",
      description="catalog and store images",
      author="Erin Call",
      author_email="hello@erincall.com",
      url="https://git.erincall.com/ErinCall/catsnap/blob/master/README.md",
      packages=['catsnap',
                'catsnap.document',
                'catsnap.config',
                'catsnap.batch'],
      scripts=['scripts/catsnap'],
      install_requires=[
          "Flask==0.9",
          "gunicorn==0.14.6",
          "boto==2.5.2",
          "requests==0.13.2",
          "argparse==1.2.1",
          "psycopg2==2.4.6",
          "sqlalchemy==0.8.0b2",
          "yoyo-migrations==4.1.6",
          "wand==0.3.3",
          "celery==3.1.16",
          "redis==2.10.3",

          "mock==1.0.1",
          "nose==1.1.2",
          "splinter==0.5.3",
          "bcrypt==1.1.1",
      ],
      )
