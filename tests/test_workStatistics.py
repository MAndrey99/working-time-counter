from unittest.mock import patch, MagicMock
from freezegun import freeze_time
from datetime import datetime, timedelta
from random import randint, random
from math import isclose
from pickle import dumps
from contextlib import contextmanager
from copy import deepcopy
from typing import *

from tests.db_utils import DatabaseManager, get_max_end_time
from database import Period
from work_statistics import WorkStatistics

DATABASE = 'sqlite:///testdb.sqlite'


@freeze_time(get_max_end_time(DATABASE))
class TestWorkStatistics:
    __slots__ = ("database_manager", )

    def setup(self):
        import database.orm as db
        self.database_manager = DatabaseManager(DATABASE)
        db.Session = self.database_manager.Session

    def teardown(self):
        self.database_manager.close_connection()

    def test_init(self):
        ws = WorkStatistics()

        for it in dir(ws):  # проходимся по приватным полям
            if it.startswith('_') and not it.endswith('__'):
                assert not ws.__getattribute__(it)

    def test_from_db(self):
        with patch('work_statistics.new_session', side_effect=self.database_manager.new_session_context) as mock:
            ws = WorkStatistics.from_db()
            mock.assert_called()

        assert ws._cache_ymwd
        assert ws._day and ws._week and ws._month and ws._year
        assert isclose(ws._day, ws.day.total_seconds()) \
            and isclose(ws._week, ws.week.total_seconds()) \
            and isclose(ws._month, ws.month.total_seconds()) \
            and isclose(ws._year, ws.year.total_seconds())

    def test_period_stat(self):
        now = datetime.now()

        def step_generator(begin: datetime) -> Iterable[datetime]:
            t = begin + timedelta(seconds=randint(1, 60*60))
            while t <= now:
                yield t
                t += timedelta(seconds=randint(60*60, 10*24*60*60))  # переходим далее на час-10 деней
                if random() < .1:
                    yield None

        def check_for(ws: WorkStatistics):
            begin = datetime.now() - timedelta(days=365)
            for it in step_generator(begin):
                start = datetime.fromtimestamp(randint(int(begin.timestamp()), int((it or now).timestamp()) - 1))
                assert isclose(
                    ws.period_stat(Period(start, it)).total_seconds(),
                    self.database_manager.get_work_time_in_period(Period(start, it))
                )

        check_for(WorkStatistics.from_db())

    def test_update(self):
        now = datetime.now()
        day_end = datetime.fromordinal(now.toordinal()) + timedelta(days=1)
        week_end = datetime(now.year, now.month, now.day) + timedelta(days=7 - now.weekday())
        month_end = datetime(now.year, now.month + 1, 1) if now.month != 12 else datetime(now.year + 1, now.month, 1)
        year_end = datetime(now.year + 1, 1, 1)

        ws = WorkStatistics.from_db()
        last_cache = {
            "day": ws._day,
            "week": ws._week,
            "month": ws._month,
            "year": ws._year
        }

        with self.database_manager.new_session_context() as session:
            @contextmanager
            def session_context(): yield session

            with patch('work_statistics.new_session', side_effect=session_context) as mock:
                with freeze_time(day_end):
                    ws.update()
                    mock.assert_called()

                assert ws._last_update == day_end
                assert ws.day.total_seconds() == ws._day == 0
                if day_end < week_end:
                    assert isclose(ws.week.total_seconds(), ws._week) and isclose(ws._week, last_cache['week'])
                if day_end < month_end:
                    assert isclose(ws.month.total_seconds(), ws._month) and isclose(ws._month, last_cache['month'])
                    assert isclose(ws.year.total_seconds(), ws._year) and isclose(ws._year, last_cache['year'])

                now = day_end + timedelta(hours=12)
                with freeze_time(now):
                    # проводим добавление данных в базу и проверяем
                    begin = randint(int(day_end.timestamp()), int(day_end.timestamp()) + 10000)
                    end = randint(begin, int(now.timestamp()))
                    length = end - begin
                    last_ws = deepcopy(ws)

                    t = session.begin_nested()
                    try:
                        session.add(Period(begin, end))
                        ws.update()
                    finally:
                        t.rollback()

                    assert ws._last_update == now
                    assert isclose(ws.day.total_seconds(), length)

                    ws = last_ws

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
                    assert ws.month.total_seconds() == ws._month == 0
                    assert ws.year.total_seconds() == ws._year == 0

                # проверяем, что в новый год не сбрасывается инфа за неделю если она не кончилась
                ws._last_update = datetime(2019, 12, 31)
                ws._week = 99
                with freeze_time(datetime(2020, 1, 1)), patch('work_statistics.new_session', MagicMock):
                    ws.update()
                assert ws.week.total_seconds() == 99

        # проверяем, что без кэша update ничего не делает и не стучится в бд
        ws = WorkStatistics()
        last = dumps(ws, protocol=4)
        with patch('work_statistics.new_session') as mock:
            ws.update()
            mock.assert_not_called()
        assert last == dumps(ws, protocol=4)

    def test_ymwd(self):
        now = datetime.now()
        day_begin = datetime.fromordinal(now.toordinal())
        week_begin = datetime(now.year, now.month, now.day) - timedelta(days=now.weekday())
        month_begin = datetime(now.year, now.month, 1)
        year_begin = datetime(now.year, 1, 1)

        for ws in (WorkStatistics.from_db(), WorkStatistics()):
            assert isclose(
                ws.day.total_seconds(),
                self.database_manager.get_work_time_in_period(Period(day_begin, now))
            )
            assert isclose(
                ws.week.total_seconds(),
                self.database_manager.get_work_time_in_period(Period(week_begin, now))
            )
            assert isclose(
                ws.month.total_seconds(),
                self.database_manager.get_work_time_in_period(Period(month_begin, now))
            )
            assert isclose(
                ws.year.total_seconds(),
                self.database_manager.get_work_time_in_period(Period(year_begin, now))
            )
