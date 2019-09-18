import sqlite3 as sqlite
from pathlib import Path
from datetime import datetime, date
from contextlib import contextmanager
from typing import *

from wtc.work_statistics import Period


class DatabaseManager:
    __slots__ = ("_connection", )

    def __init__(self, database: str):
        assert Path(database).is_file()
        self._connection = sqlite.connect(database)

    def close_connection(self):
        self._connection.close()

    @contextmanager
    def auto_rollback_connection_context(self) -> ContextManager[sqlite.Connection]:
        with self._connection as conn:
            yield conn
            conn.rollback()  # TODO: должно работать...

    def get_period_length(self, begin: Union[int, float, date, datetime], end: Union[int, float, date, datetime]) -> int:
        if type(begin) is not int:
            if type(begin) is float:
                begin = int(begin)
            elif type(begin) is datetime or type(begin) is date:
                begin = int(begin.timestamp())
            else:
                raise ValueError

        if type(end) is not int:
            if type(end) is float:
                end = int(end)
            elif type(end) is datetime or type(end) is date:
                end = int(end.timestamp())
            else:
                raise ValueError

        return self._connection.execute(
            f"select sum(min({end}, last_timestamp) - max({begin}, first_timestamp)) "
            f"from active_time "
            f"where last_timestamp > {begin} and first_timestamp < {end}"
        ).fetchone()[0] or 0

    def add_period(self, period: Period):
        """
        добавляет указаный промежуток времени в базу
        """

        pass  # TODO
