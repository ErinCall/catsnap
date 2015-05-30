# Catsnap

Catsnap is a tool for managing your pictures. Never again will you lose your collection to a faulty hard drive. Never again will you run into upload limits, bandwidth maximums, or service closures.

## How it works

Catsnap uses Amazon S3 and a PostgreSQL database to store and organize your images. Images are hosted for public access on S3, and each image can have one or more tags associated with it. Images can also be in an album, to organize sets of related images.

Once you store an image, you can look it up by its tags or album. Easy!

If you like, you can [check out my Catsnap instance](https://catsnap.andrewlorente.com>) to see what it looks like once running.

## Setting up Catsnap

Catsnap uses a web service to provide you access to your images. Let's walk through the process of getting it set up.

First, you'll need to create [an Amazon WebServices account](https://aws.amazon.com/), if you don't already have one. This may take a bit of time, so be patient. Amazon will require a credit card, but the cost of running Catsnap will be tiny--a few cents a month, typically.

Once you have an AWS account, you can [create a bucket](https://console.aws.amazon.com/s3/home) in S3 where your images will be stored. Pick a name that makes sense to you--I use "catsnap-andrewlorente".

Optionally, you may wish to [create a cloudfront distribution](https://console.aws.amazon.com/cloudfront/home) so people can download your images lightning-fast.

Now that you've got your S3 bucket set up, you'll want a Catsnap server. Catsnap is a snap to set up on your own server, and this guide assumes you'll do that. If you don't already have a server, Catsnap fits easily on a $5/month [Digital Ocean](https://www.digitalocean.com/) VPS. You can also run Catsnap on [Heroku](https://www.heroku.com/), but you'll need to pay for a worker dyno.

You'll need to figure out a couple of things on your own:

* A web server. I run Catsnap behind [Nginx](http://nginx.org/); while you could put Catsnap right on port 80, it is not recommended.
* [Postgresql](http://www.postgresql.org/) and [Redis](http://redis.io/) instances will need to be available. You can just run them on the same server, if you like. Catsnap won't work them very hard.
* A deploy strategy. I really like [Fabric](http://www.fabfile.org/) for deployment.

Whatever deploy system you choose, it'll need to perform at least these tasks:

* Get the latest code onto the server.
* Install dependencies, with `python setup.py develop`.
* Run any needed migrations, with `yoyo-migrate -b apply migrations $DATABASE_URL`.
* Re/start the web process, with `gunicorn catsnap.app:app -b 0.0.0.0:$PORT`.
* Re/start the worker process, with `celery -A catsnap.worker worker`.

Outside your deploy process, you'll need to add some Catsnap configuration. In keeping with the [12-factor app](http://12factor.net/) philosophy, Catsnap will tend to look for environment variables. You can have your deploy system set them up in the web user's environment, or just point a variable called ENV at a file containing environment variables and they'll be merged into Catsnap's environment. Catsnap uses the following environment variables:

* `DATABASE_URL` is the [Postgresql database connection URI](http://www.postgresql.org/docs/9.2/static/libpq-connect.html#AEN38208) for your Catsnap database.
* `CATSNAP_CELERY_BROKER_URL` is the [URI for a Redis instance](http://celery.readthedocs.org/en/latest/getting-started/brokers/redis.html) that Catsnap can use.
* `CATSNAP_API_KEY` is a secret key the client and server share for authentication. It can be any string of characters. You should keep it secret!
* `CATSNAP_AWS_ACCESS_KEY_ID` and `CATSNAP_AWS_SECRET_ACCESS_KEY`: find the values for these two variables [on your AWS account page](https://portal.aws.amazon.com/gp/aws/securityCredentials#access_credentials).
* `CATSNAP_BUCKET`: the S3 bucket that you set up earlier.
* `CATSNAP_SECRET_KEY`: a secret key to use when generating session identifiers. Like the API key, this can be any string of characters, and should be kept secret.
* `CATSNAP_PASSWORD_HASH`: a bcrypt-hashed password you want to use to log in. You can generate a password hash by running `python -c 'import bcrypt, sys; print bcrypt.hashpw(sys.stdin.readline().strip(), bcrypt.gensalt())'` and typing the password you want to hash.
* `CATSNAP_CLOUDFRONT_DISTRIBUTION_ID` (optional): the id of your cloudfront distribution, if you made one. Note this is different from the XXXX.cloudfront.net domain; you want to get it from your AWS console.
* `EMAIL_HOST`, `ERROR_RECIPIENT`, `ERROR_SENDER` (optional, but include all or none): an SMTP host and email addresses to/from which to send error emails
* `EMAIL_USERNAME` and `EMAIL_PASSWORD` (optional): if the SMTP server in `EMAIL_HOST` requires login credentials, these are those credentials.

Now your Catsnap server is all set up! Navigate to your server and you're ready to start adding images.

## Using Catsnap

It is very straightforward to use the web interface. Search in the search box to find images you've previously stored. Use the upload or upload-by-url inputs to add new images.
