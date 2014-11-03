from __future__ import unicode_literals

from catsnap.web import delayed_tasks

def delay(task, *args, **kwargs):
    delayed_tasks.append((task, args, kwargs))
