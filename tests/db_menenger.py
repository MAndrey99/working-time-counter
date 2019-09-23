from sqlalchemy.sql import func as sqlFunc
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
        total_time = self.session.query(sqlFunc.sum(sqlFunc.min(p.end, Period.end) - sqlFunc.max(p.begin, Period.begin)))\
            .filter((Period.end > p.begin) & (Period.begin < p.end))\
            .first()[0]
        return 0 if total_time is None else int(total_time)

    def add_period(self, period: Period):
        """
        добавляет указаный промежуток времени в базу
        """

        pass  # TODO
