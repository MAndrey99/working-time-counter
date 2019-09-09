from pytest import fail, raises
from wtc.work_statistics_monitor import WorkStatistics

DATABASE = 'testdb.sqlite'


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
        fail()  # TODO

    def test_update(self):
        fail()  # TODO

    def test_ymwd(self):
        fail()  # TODO
