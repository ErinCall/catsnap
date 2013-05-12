import sys
import traceback

class ExceptionLogger(object):
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except Exception:
            (exc_type, exc_value, trace) = sys.exc_info()
            traceback.print_exception(exc_type,
                                      exc_value,
                                      trace,
                                      file=sys.stdout)
            raise
