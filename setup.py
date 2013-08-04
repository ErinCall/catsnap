#!/usr/bin/python

from setuptools import setup

setup(name="catsnap",
      version="4.2.0",
      description="catalog and store images",
      author="Andrew Lorente",
      author_email="andrew.lorente@gmail.com",
      url="github.com/andrewlorente/catsnap",
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
          "flask-openid==1.1.1",
          "psycopg2==2.4.6",
          "sqlalchemy==0.8.0b2",
          "yoyo-migrations==4.1.6",
          "PIL==1.1.7",
          "wand",
          'Flask-Assets',
          'jsmin',
          'cssmin',

          "mock==0.8",
          "nose==1.1.2",
          "splinter==0.5.3",
      ],
      )
