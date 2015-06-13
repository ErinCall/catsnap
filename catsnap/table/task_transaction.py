from __future__ import unicode_literals

import uuid
from sqlalchemy import (
    Column,
    String,
    DateTime,
    func,
    and_,
    or_,
    ForeignKey,
    LargeBinary,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.declarative import declarative_base
Base = declarative_base()
from catsnap import Client

class TaskTransaction(Base):
    __tablename__ = 'task_transaction'

    transaction_id = Column(UUID(as_uuid=True), primary_key=True)

    @classmethod
    def new_id(cls):
        transaction_id = uuid.uuid4()
        Client().session().add(cls(transaction_id=transaction_id))
        return transaction_id

