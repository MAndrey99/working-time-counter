import sqlite3 as sqlite
from datetime import datetime, timedelta
from dataclasses import dataclass


@dataclass(frozen=True)
class Period:
    begin: datetime
    end: datetime


class WorkStatistics:
    __slots__ = ('_periods', )

    @staticmethod
    def from_db(db) -> 'WorkStatistics':
        periods = []

        conn: sqlite.Connection
        with sqlite.connect(db) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(f'SELECT first_timestamp, last_timestamp FROM active_time ORDER BY first_timestamp')
            except sqlite.OperationalError:
                res = WorkStatistics()
                res._periods = periods
                return res

            for begin, end in cursor.fetchall():
                periods.append(Period(datetime.fromtimestamp(begin), datetime.fromtimestamp(end)))

        res = WorkStatistics()
        res._periods = periods
        return res

    def period_stat(self, begin: datetime, end: datetime) -> timedelta:
        assert end > begin
        res = timedelta()

        for period in (
                Period(max(begin, it.begin), min(end, it.end))
                for it in self._periods
                if it.end > begin and it.begin < end
        ):
            res += period.end - period.begin

        return res

    def year_stat(self) -> timedelta:
        now = datetime.now()
        return self.period_stat(datetime(now.year, 1, 1), now)

    def month_stat(self) -> timedelta:
        now = datetime.now()
        return self.period_stat(datetime(year=now.year, month=now.month, day=1), now)

    def week_stat(self) -> timedelta:
        now = datetime.now()
        return self.period_stat(
            now - timedelta(
                days=now.weekday(),
                hours=now.hour,
                minutes=now.minute,
                seconds=now.second,
                microseconds=now.microsecond
            ),
            now
        )
