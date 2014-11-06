from __future__ import unicode_literals

from flask import g

def delay(task, *args, **kwargs):
    g.delayed_tasks.append((task, args, kwargs))
