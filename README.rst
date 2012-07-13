Catsnap
======

Catsnap is a tool for managing your pictures. Never again will you find yourself without the perfect cat gif or image macro to express your feelings!

How it works
------------

Catsnap uses Amazon S3 and DynamoDb to store and organize your images. Images are hosted for public access on S3, and each image can have one or more tags associated with it.

Once you store an image, you can look it up by its tags. Easy!

Installation and Setup
----------------------

* install catsnap: ``pip install catsnap``
* This may install catsnap to ``/usr/local/share/python``. If you're getting 'command not found' errors, make sure catsnap is in your $PATH by adding this line to your ``.bashrc`` or ``.bash_profile``:
  - ``export PATH=/usr/local/share/python:$PATH``
* `Sign up for an Amazon Web Services account <https://aws-portal.amazon.com/gp/aws/developer/registration/index.html>`_.
* Make sure you're signed up for S3 and DynamoDB (you typically are by default).
* run ``catsnap setup`` and the catsnap script will take care of all other setup.

Using Catsnap
-------------

Add an image:
    ``catsnap add http://i.imgur.com/zqCWA.gif dancing cat kitten``
Find an image by tag:
    ``catsnap find kitten``
