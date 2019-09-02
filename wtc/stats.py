import sqlite3 as sqlite
from datetime import datetime, timedelta
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Period:
    begin: datetime
    end: datetime


class WorkStatistics:
    __slots__ = ('_periods', )

    @staticmethod
    def from_db(db) -> 'WorkStatistics':
        conn: sqlite.Connection
        with sqlite.connect(db) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    f'SELECT first_timestamp, last_timestamp '
                    f"FROM active_time WHERE last_timestamp > {datetime(datetime.now().year, 1, 1).timestamp()} "
                    f'ORDER BY first_timestamp'
                )
            except sqlite.OperationalError as e:
                res = WorkStatistics()
                res._periods = tuple()
                return res

        res = WorkStatistics()
        res._periods = tuple((
                Period(datetime.fromtimestamp(begin), datetime.fromtimestamp(end))
                for begin, end in cursor.fetchall()
        ))
        return res

    def period_stat(self, begin: datetime, end: Optional[datetime] = None) -> timedelta:
        assert end is None or end > begin

        if end is None:
            def period_important_part(period: Period) -> float:
                return period.end.timestamp() - max(begin, period.begin).timestamp()
        else:
            def period_important_part(period: Period) -> float:
                return min(end, period.end).timestamp() - max(begin, period.begin).timestamp()

        return timedelta(seconds=sum(
                period_important_part(it)
                for it in self._periods
                if it.end > begin and (end is None or it.begin < end)
        ))

    @property
    def year(self) -> timedelta:
        return self.period_stat(datetime(datetime.now().year, 1, 1))

    @property
    def month(self) -> timedelta:
        now = datetime.now()
        return self.period_stat(datetime(year=now.year, month=now.month, day=1))

    @property
    def week(self) -> timedelta:
        now = datetime.now()
        return self.period_stat(
            now - timedelta(
                days=now.weekday(),
                hours=now.hour,
                minutes=now.minute,
                seconds=now.second,
                microseconds=now.microsecond
            )
        )

    @property
    def day(self) -> timedelta:
        now = datetime.now()
        return self.period_stat(datetime(now.year, now.month, now.day))
