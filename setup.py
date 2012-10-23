#!/usr/bin/python

from setuptools import setup

setup(name="catsnap",
      version="2.3.0",
      description="catalog and store funny pictures",
      author="Andrew Lorente",
      author_email="andrew.lorente@gmail.com",
      url="github.com/andrewlorente/catsnap",
      packages=['catsnap',
                'catsnap.document',
                'catsnap.config',
                'catsnap.batch'],
      scripts=['scripts/catsnap'],
      install_requires=[
          "boto==2.5.2",
          "requests==0.13.2",
          "argparse==1.2.1",

          "mock==0.8",
          "nose==1.1.2",
          ],
      )
