from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from typing import *

from database import new_session, Session, Period


class DatabaseManager:
    __slots__ = ("Session", "session", "_transaction", "_connection")

    def __init__(self, database: str):
        # используется транзакция вне orm
        self._connection = create_engine(database).connect()
        self._transaction = self._connection.begin()
        self.Session = sessionmaker(bind=self._connection)
        self.session = self.Session()

    def close_connection(self):
        self._transaction.rollback()
        self._connection.close()

    @contextmanager
    def new_session_context(self) -> ContextManager[Session]:
        with new_session() as session:
            yield session
            session.rollback()

    def get_work_time_in_period(self, p: Period) -> int:
        return sum(
            (min(it.end, p.end) - max(it.begin, p.begin)).total_seconds()
            for it in self.session.query(Period).filter(
                    # str по тому что в sqlite datetime хранится как строка
                    (Period.end > str(p.begin)) & (Period.begin < str(p.end))
                )
        )
