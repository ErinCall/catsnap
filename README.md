# Catsnap

Catsnap is a tool for managing your pictures. Never again will you lose your collection to a faulty hard drive. Never again will you run into upload limits, bandwidth maximums, or service closures.

## How it works

Catsnap uses Amazon S3 and a PostgreSQL database to store and organize your images. Images are hosted for public access on S3, and each image can have one or more tags associated with it. Images can also be in an album, to organize sets of related images.

Once you store an image, you can look it up by its tags or album. Easy!

If you like, you can [check out my Catsnap instance](https://catsnap.erincall.com) to see what it looks like when running.

## Setting up Catsnap

Catsnap uses a web service to provide you access to your images. Let's walk through the process of getting it set up.

First, you'll need to create [an Amazon WebServices account](https://aws.amazon.com/), if you don't already have one. This may take a bit of time, so be patient. Amazon will require a credit card, but the cost of running Catsnap will be tiny--a few cents a month, typically.

Once you have an AWS account, you can [create a bucket](https://console.aws.amazon.com/s3/home) in S3 where your images will be stored. Pick a name that makes sense to you. You may also want a second bucket for local/development use.

Optionally, you may wish to [create a cloudfront distribution](https://console.aws.amazon.com/cloudfront/home) so people can download your images lightning-fast.

### Running locally

You need python 2.7. Clone the repo and run `python setup.py develop` to fetch the requirements.

Catsnap depends on [Postgresql](http://www.postgresql.org/) and [Redis](http://redis.io/), so make sure they're installed and running. Next you need to do some configuration. Copy [catsnap/config/example.config.yml](catsnap/config/example.config.yml) to `catsnap/config/config.yml` and read through it. Most of the example settings will be fine for development, but you'll need to make a couple of changes. There are instructions in the example config.

You're nearly ready! Create a postgres database for catsnap to use, and set up its schema by running `yoyo-migrate -b apply migrations postgresql://localhost/catsnap` (you may need to edit that database url, depending on your postgres configuration).

You're good to go! Start the web service with `gunicorn -k flask_sockets.worker catsnap.app:app -b 0.0.0.0:5000` and the background worker with `celery -A catsnap.worker worker` and visit [localhost:5000](http://localhost:5000) to get snapping!

### Running in production

Production use is pretty similar to dev. There are a couple of caveats:

If you'll be putting Catsnap behind a reverse proxy like [Nginx](http://nginx.org), be sure to tell it to [forward HTTP Upgrade headers](http://nginx.org/en/docs/http/websocket.html) to catsnap's `/task_info` route.

If you're using Heroku, you won't be able to deploy a `config.yml`. You can configure catsnap with environment variables (`heroku config`); see `example.config.yml` for instructions on translating option names to env vars.
