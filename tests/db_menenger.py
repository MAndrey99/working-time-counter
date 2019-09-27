from contextlib import contextmanager
from typing import *

from database import new_session, Session, Period


class DatabaseManager:
    __slots__ = ("session", )

    def __init__(self):
        self.session = new_session()

    def close_connection(self):
        self.session.rollback()

    @contextmanager
    def new_session_context(self) -> ContextManager[Session]:
        session = new_session()
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
