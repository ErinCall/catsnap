Catsnap
======

Catsnap is a tool for managing your pictures. Never again will you find yourself without the perfect cat gif or image macro to express your feelings!

How it works
------------

Catsnap uses Amazon S3 and DynamoDb to store and organize your images. Images are hosted for public access on S3, and each image can have one or more tags associated with it.

Once you store an image, you can look it up by its tags. Easy!

Installation and Setup
----------------------

* install catsnap using `pip <http://pypi.python.org/pypi/pip/>`_: ``pip install catsnap``
* Depending on your python setup, this may install catsnap to ``/usr/local/share/python``. Most people will have no problem, but if you're getting 'command not found' errors, make sure catsnap is in your ``$PATH`` by adding this line to your ``.bashrc`` or ``.bash_profile``:
  - ``export PATH=/usr/local/share/python:$PATH``
* `Sign up for an Amazon Web Services account <https://aws-portal.amazon.com/gp/aws/developer/registration/index.html>`_ (or use your existing account).
* Make sure you're signed up for S3 and DynamoDB (you typically are by default).
* run ``catsnap setup`` and the catsnap script will walk you through configuring the necessary options.

Using Catsnap
-------------

Add an image:

    ``catsnap add http://i.imgur.com/zqCWA.gif dancing cat kitten``

Find an image by tag:

    ``catsnap find kitten``

Configuring Catsnap
-------------------

Catsnap supports configuration in 3 ways: environment variable, config file, and command-line argument. Command-line flags override config file settings, which override environment variables. Variables in each environment look slightly different:

    ``export CATSNAP_AWS_ACCESS_KEY_ID=itsme``
    ``catsnap --aws-access-key-id=itsme ...``
    ``echo 'aws_access_key_id = itsme' >> ~/.catsnap`` (this is not strictly correct; the setting needs to be in the correct section. It is best to use ``catsnap config`` to edit your ~/.catsnap)

How Catsnap interacts with your AWS account
-------------------------------------------

Catsnap requires `an S3 bucket <http://aws.amazon.com/s3/>`_ to host your images. You can use an existing bucket, or Catsnap can create one for you. The name of the bucket will be visible in your image urls if you send them to other people, so don't choose something embarassing!

Catsnap also creates two dynamodb tables. Dynamodb doesn't offer namespaced tables, so the tables' names are prefixed with your bucket name. This should prevent catsnap from conflicting with any of your other tables' names.

