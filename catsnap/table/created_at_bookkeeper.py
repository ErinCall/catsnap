import time
from sqlalchemy import Column, DateTime
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()


class CreatedAtBookkeeper(Base):
    __abstract__ = True

    created_at = Column(DateTime)

    def __init__(self, *args, **kwargs):
        super(CreatedAtBookkeeper, self).__init__(*args, **kwargs)
        if not self.created_at:
            self.created_at = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
