Catsnap
=======

Catsnap is a tool for managing your pictures. Never again will you find yourself without the perfect cat gif or image macro to express your feelings!

How it works
------------

Catsnap uses Amazon S3 and a PostgreSQL database to store and organize your images. Images are hosted for public access on S3, and each image can have one or more tags associated with it.

Once you store an image, you can look it up by its tags. Easy!

If you like, you can `check out my catsnap instance <http://catsnap.andrewlorente.com>`_ to see what it looks like once running.

Setting up Catsnap
------------------

Catsnap has two pieces that work together: a webserver and a command-line client. You can use the webserver by itself, or use both. You cannot use just the command-line client, because it needs to interact with the services the webserver provides.

First, you'll need to create `an Amazon WebServices account <https://aws.amazon.com/>`_, if you don't already have one. This may take a bit of time, so be patient. Amazon will require a credit card, but the cost of running catsnap will be tiny--a few cents a month, at most.

Once you have an AWS account, you can `create a bucket <https://console.aws.amazon.com/s3/home>`_ in S3 where your images will be stored. Pick a name that makes sense to you--I use "catsnap-andrewlorente".

Now that you've got your S3 bucket set up, you'll want a catsnap server. Catsnap is a snap to set up on Heroku, and this guide assumes you'll do that. You can also run it on your own server, if you prefer.

To run catsnap on Heroku, you'll first need to sign up. Like Amazon, Heroku will want your credit card information, but you'll be able to run catsnap on their free tier.  Heroku has `an excellent getting-started guide <https://devcenter.heroku.com/articles/quickstart>`_. Go ahead and follow the first few steps of that, until you can successfully run ``heroku login``.

Running a heroku app requires having a local checkout of your code. Clone Catsnap from Github:

    ``git clone git@github.com:AndrewLorente/catsnap.git``

Change into the catsnap directory and use the heroku toolkit to create a new app:

    ``heroku create``

Deploy catsnap to Heroku:

    ``git push heroku master``

Now create a free-tier Postgres database for Catsnap to use:

    ``heroku addons:add heroku-postgresql:dev``

The output from this command will include a line like:

    ``Attached as HEROKU_POSTGRESQL_RED``

Promote that database to production (replace "COLOR" with the correct color from the previous command's output):

    ``heroku pg:promote HEROKU_POSTGRESQL_COLOR_URL``

Have Catsnap set the database up with the tables you need, and your database is ready to go:

    ``heroku run yoyo-migrate apply migrations '$DATABASE_URL'``

The last thing you'll need to do is configure Catsnap for your personal use. Configure all of the following environment variables with ``heroku config:set VARIABLE_NAME value``
    * CATSNAP_API_KEY is a secret key the client and server share for authentication. It can be any string of characters. You should keep it secret!
    * CATSNAP_AWS_ACCESS_KEY_ID and CATSNAP_AWS_SECRET_ACCESS_KEY: find the values for these two variables `on your AWS account page <https://portal.aws.amazon.com/gp/aws/securityCredentials#access_credentials>`_.
    * CATSNAP_BUCKET: the S3 bucket that you set up earlier.
    * CATSNAP_SECRET_KEY: a secret key to use when generating session identifiers. Like the API key, this can be any string of characters.
    * CATSNAP_OWNER_ID: an OpenID provider that identifies you as the owner of this catsnap installation. I recommend using your Google account, in which case you would set this to ``https://www.google.com/accounts/o8/id``.
    * CATSNAP_OWNER_EMAIL: the email address associated with your OpenID url.

Now your catsnap server is all set up! Navigate to the url for your Heroku app and you're ready to start adding images.

Setting up the catsnap command-line client takes very little time. CD into your catsnap directory and run ``python setup.py install`` to install the client. Then run ``catsnap config`` and follow the prompts to configure the client.

Using Catsnap
-------------

It is very straightforward to use the web interface. Search in the search box to find images you've previously stored. Use the upload or upload-by-url inputs to add new images.

The command-line client is similarly simple. There are two main commands you'll run: ``catsnap add`` and ``catsnap find``.

``catsnap add`` takes as its arguments an image by url or filename and a series of tags to associate with that image.

``catsnap find`` takes as its arguments one or more tags to find, and finds all images that match any of those tags.

