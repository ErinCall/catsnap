Catsnap
======

Catsnap is a tool for managing your pictures. Never again will you find yourself without the perfect cat gif or image macro to express your feelings!

How it works
------------

Catsnap uses Amazon S3 and DynamoDb to store and organize your images. Images are hosted for public access on S3. Each image can have one or more tags associated with it.

Installation
------------

* git clone https://github.com/AndrewLorente/catsnap.git
* cd catsnap
* python setup.py install

Using Catsnap
-------------

Add an image:
    ``catsnap add http://i.imgur.com/zqCWA.gif dancing cat kitten``
Find an image by tag:
    ``catsnap find kitten``
