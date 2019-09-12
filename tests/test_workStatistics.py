import sqlite3 as sqlite
from pytest import raises, skip
from freezegun import freeze_time
from wtc.work_statistics_monitor import WorkStatistics
from datetime import datetime, date, timedelta
from random import randint
from typing import *

DATABASE = 'testdb.sqlite'


def sql_period_length_call(
        conn: sqlite.Connection,
        begin: Union[int, float, date, datetime],
        end: Union[int, float, date, datetime]):

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

    return conn.execute(
                f"select sum(min({end}, last_timestamp) - max({begin}, first_timestamp)) "
                f"from active_time "
                f"where last_timestamp > {begin} and first_timestamp < {end}"
            ).fetchone()[0] or 0


@freeze_time(lambda: datetime.fromtimestamp(1567633936))
class TestWorkStatistics:
    def test_init(self):
        ws = WorkStatistics()

        for it in dir(ws):
            if it.startswith('_') and not it.endswith('__'):
                assert ws.__getattribute__(it) is None or not ws.__getattribute__(it)

    def test_from_db(self):
        with raises(FileNotFoundError):
            WorkStatistics.from_db('_' + DATABASE)

        ws = WorkStatistics.from_db(DATABASE)
        assert ws._cache_ymwd
        assert ws._day and ws._week and ws._month and ws._year
        assert ws._day == ws.day.total_seconds() \
               and ws._week == ws.week.total_seconds() \
               and ws._month == ws.month.total_seconds() \
               and ws._year == ws.year.total_seconds()

        ws = WorkStatistics.from_db(DATABASE, cache_ymwd=False)
        assert not ws._cache_ymwd
        assert ws._day is None and ws._week is None and ws._month is None and ws._year is None
        assert ws.year >= ws.month >= ws.week >= ws.day

    def test_period_stat(self):
        def step_generator(begin: datetime) -> Iterable[datetime]:
            t = begin
            t += timedelta(seconds=randint(2, 15))
            while t <= datetime.now():
                yield t
                t += timedelta(seconds=randint(50, 500))

        ws = WorkStatistics.from_db(DATABASE)
        conn = sqlite.connect(DATABASE)
        begin = datetime.now() - timedelta(days=365)
        for it in step_generator(begin):
            start = datetime.fromtimestamp(randint(begin.timestamp(), it.timestamp() - 1))
            ps = ws.period_stat(start, it)
            assert ps.total_seconds() == sql_period_length_call(conn, start, it)

        # TODO: то же, но без кэша

    def test_update(self):
        skip('TODO')

    def test_ymwd(self):
        now = datetime.now()
        day_begin = datetime.fromordinal(now.toordinal())
        week_begin = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        month_begin = datetime(now.year, now.month, 1)
        year_begin = datetime(now.year, 1, 1)

        conn = sqlite.connect(DATABASE)
        ws = WorkStatistics.from_db(DATABASE)

        assert ws.day.total_seconds() == sql_period_length_call(conn, day_begin, now)
        assert ws.week.total_seconds() == sql_period_length_call(conn, week_begin, now)
        assert ws.month.total_seconds() == sql_period_length_call(conn, month_begin, now)
        assert ws.year.total_seconds() == sql_period_length_call(conn, year_begin, now)

        # TODO: то же, но без кэша
