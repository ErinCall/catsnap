#!/usr/bin/python

from setuptools import setup

setup(name="catsnap",
      version="5.0.1",
      description="catalog and store images",
      author="Andrew Lorente",
      author_email="andrew.lorente@gmail.com",
      url="https://git.andrewlorente.com/AndrewLorente/catsnap/blob/master/README.rst",
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
          "flask-openid==1.2.3",
          "psycopg2==2.4.6",
          "sqlalchemy==0.8.0b2",
          "yoyo-migrations==4.1.6",
          "wand==0.3.3",
          "celery==3.1.16",
          "redis==2.10.3",

          "mock==1.0.1",
          "nose==1.1.2",
          "splinter==0.5.3",
      ],
      )
