from __future__ import unicode_literals

import os
import subprocess

## OK SO

# here's how I want this to work
# When the application starts and is in debug mode, it should fork off a
# webpack dev server.
# When the application starts and is not in debug mode, it should assume
# webpack has already run (since it might take a few seconds, and we don't
# want to wait to get a-servin').
# Either way there will need to be some sort of all_the_javascripts function
# available in templates.

class Webpack(object):
    def init_app(self, app):
        if app.debug:
            subprocess.Popen(
                [os.path.join(os.path.dirname(__file__),
                                          'build',
                                          'node_modules',
                                          '.bin',
                                          'webpack-dev-server')],
                stdin=subprocess.PIPE,
                cwd=os.path.join(os.path.dirname(__file__), 'build'),
            )
        else:
            pass
