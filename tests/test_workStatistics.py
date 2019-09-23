from unittest.mock import patch
from freezegun import freeze_time
from datetime import datetime, timedelta
from random import randint
from math import isclose
from typing import *

from .db_menenger import DatabaseManager
from database import Period, init as initORM
from work_statistics import WorkStatistics

DATABASE = 'sqlite:///tests/testdb.sqlite'


@freeze_time('2019-09-21 13:53:42.379014')
class TestWorkStatistics:
    __slots__ = ("database_manager", )

    def setup(self):
        initORM(DATABASE)
        self.database_manager = DatabaseManager()

    def teardown(self):
        self.database_manager.close_connection()

    def test_init(self):
        ws = WorkStatistics()

        for it in dir(ws):  # проходимся по приватным полям
            if it.startswith('_') and not it.endswith('__'):
                assert not ws.__getattribute__(it)

    def test_from_db(self):
        with patch('work_statistics.new_session', return_value=self.database_manager.session):
            ws = WorkStatistics.from_db()

        assert ws._cache_ymwd
        assert ws._day and ws._week and ws._month and ws._year
        assert isclose(ws._day, ws.day.total_seconds()) \
               and isclose(ws._week, ws.week.total_seconds()) \
               and isclose(ws._month, ws.month.total_seconds()) \
               and isclose(ws._year, ws.year.total_seconds())

        with patch('work_statistics.new_session', return_value=self.database_manager.session):
            ws = WorkStatistics.from_db(cache_ymwd=False)

        assert not ws._cache_ymwd
        assert ws._day is None and ws._week is None and ws._month is None and ws._year is None
        assert ws.year >= ws.month >= ws.week >= ws.day

    def test_period_stat(self):
        def step_generator(begin: datetime) -> Iterable[datetime]:
            t = begin + timedelta(seconds=randint(2, 15))
            while t <= datetime.now():
                yield t
                t += timedelta(seconds=randint(60, 600))

        for ws in (WorkStatistics.from_db(), WorkStatistics.from_db(cache_ymwd=False)):
            begin = datetime.now() - timedelta(days=365)
            for it in step_generator(begin):
                start = datetime.fromtimestamp(randint(int(begin.timestamp()), int(it.timestamp()) - 1))
                ps = ws.period_stat(start, it)
                assert isclose(ps.total_seconds(), self.database_manager.get_work_time_in_period(Period(start, it)))

    def test_update(self):
        now = datetime.now()
        day_end = datetime.fromordinal(now.toordinal()) + timedelta(days=1)
        week_end = datetime(now.year, now.month, now.day) + timedelta(days=7 - now.weekday())
        month_end = datetime(now.year, now.month + 1, 1) if now.month != 12 else datetime(now.year + 1, now.month, 1)
        year_end = datetime(now.year + 1, 1, 1)

        # проверяем девалидацию и пересчет кэша
        ws = WorkStatistics.from_db()
        last_cache = {
                "day": ws._day,
                "week": ws._week,
                "month": ws._month,
                "year": ws._year
        }

        with self.database_manager.new_session_context() as session,\
                patch('wtc.database.new_session', return_value=session):

            with freeze_time(day_end):
                ws.update()
                assert ws.day.total_seconds() == ws._day == 0
                if day_end < week_end:
                    assert isclose(ws.week.total_seconds(), ws._week) and isclose(ws._week, last_cache['week'])
                if day_end < month_end:
                    assert isclose(ws.month.total_seconds(), ws._month) and isclose(ws._month, last_cache['month'])
                    assert isclose(ws.year.total_seconds(), ws._year) and isclose(ws._year, last_cache['year'])

            with freeze_time(week_end):
                ws.update()
                assert ws.day.total_seconds() == ws._day == 0
                assert ws.week.total_seconds() == ws._week == 0
                if week_end < month_end:
                    assert isclose(ws.month.total_seconds(), ws._month) and isclose(ws._month, last_cache['month'])
                    assert isclose(ws.year.total_seconds(), ws._year) and isclose(ws._year, last_cache['year'])

            with freeze_time(month_end):
                ws.update()
                assert ws.day.total_seconds() == ws._day == 0
                assert ws.week.total_seconds() == ws._week == 0
                assert ws.month.total_seconds() == ws._month == 0

            with freeze_time(year_end):
                ws.update()
                assert ws.day.total_seconds() == ws._day == 0
                assert ws.week.total_seconds() == ws._week == 0
                assert ws.month.total_seconds() == ws._month == 0
                assert ws.year.total_seconds() == ws._year == 0

        # TODO: смоделировать добавление данных в базу и реализовать проверку без кэширования

    def test_ymwd(self):
        now = datetime.now()
        day_begin = datetime.fromordinal(now.toordinal())
        week_begin = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        month_begin = datetime(now.year, now.month, 1)
        year_begin = datetime(now.year, 1, 1)

        for ws in (WorkStatistics.from_db(), WorkStatistics.from_db(cache_ymwd=False)):
            assert isclose(ws.day.total_seconds(), self.database_manager.get_work_time_in_period(Period(day_begin, now)))
            assert isclose(ws.week.total_seconds(), self.database_manager.get_work_time_in_period(Period(week_begin, now)))
            assert isclose(ws.month.total_seconds(), self.database_manager.get_work_time_in_period(Period(month_begin, now)))
            assert isclose(ws.year.total_seconds(), self.database_manager.get_work_time_in_period(Period(year_begin, now)))
