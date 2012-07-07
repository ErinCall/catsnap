#!/usr/bin/python

from setuptools import setup

setup(name="catsnap",
      version="0.0.1",
      description="catalog and store funny pictures",
      author="Andrew Lorente",
      author_email="andrew.lorente@gmail.com",
      packages=['catsnap'],
      install_requires=[
          "boto==2.5.2",

          "mock==1.0.0a2",
          "nose==1.1.2",
          ],
      )
