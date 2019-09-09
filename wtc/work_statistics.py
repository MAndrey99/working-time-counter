import sqlite3 as sqlite
from datetime import datetime, date, timedelta
from dataclasses import dataclass
from pathlib import Path
from typing import *

year_begin: Optional[int] = None
month_begin: Optional[int] = None
week_begin: Optional[int] = None
day_begin: Optional[int] = None


@dataclass(frozen=True)
class Period:
    begin: datetime
    end: datetime


class WorkStatistics:
    __slots__ = ('_periods', '_cache_ymwd', '_year', '_month', '_week', '_day', '_last_update', '_db')

    def __init__(self):
        self._last_update: Optional[datetime] = None  # время последнего обновления данных из бд
        self._periods: List[Period] = []  # список периодов работы за максимальный рассматриваемый срок
        self._db: str = ""  # путь/имя базы данных
        self._cache_ymwd: bool = False  # используется ли кэширование рассчитанного отработаного времени
        self._year: Optional[int] = None  # количество отработанного времени в году (сек)
        self._month: Optional[int] = None  # количество отработанного времени в месяце (сек)
        self._week: Optional[int] = None  # количество отработанного времени в неделе (сек)
        self._day: Optional[int] = None  # количество отработанного времени в дне (сек)

    @staticmethod
    def from_db(db: str, *, cache_ymwd=True) -> 'WorkStatistics':
        """
        загрузка данных из базы и создание экземпляра WorkStatistics

        :param db: имя/путь базы
        :param cache_ymwd: требуется ли кэшировать статистику за год, месяц, неделю, день
        :return: WorkStatistics со считанной из бд информацией
        """
        if not Path(db).is_file():
            raise FileNotFoundError(f'файл {db} не найден')

        global year_begin, month_begin, week_begin, day_begin

        mk_period: Callable[[datetime, datetime], Period]
        year = 0
        month = 0
        week = 0
        day = 0
        last_update: Optional[datetime] = None

        if cache_ymwd:
            now = date.today()
            year_begin = datetime(now.year, 1, 1).timestamp()
            month_begin = datetime(now.year, now.month, 1).timestamp()
            week_begin = datetime.fromordinal((now - timedelta(now.weekday())).toordinal()).timestamp()
            day_begin = datetime.fromordinal(now.toordinal()).timestamp()
            del now

            def mk_period(begin: datetime, end: datetime):
                nonlocal year, month, week, day, last_update
                assert end > begin

                begin_timestamp = begin.timestamp()
                end_timestamp = end.timestamp()
                assert end_timestamp <= datetime.now().timestamp()
                assert last_update is None or last_update <= begin
                last_update = end

                year += max(end_timestamp - max(begin_timestamp, year_begin), 0)
                month += max(end_timestamp - max(begin_timestamp, month_begin), 0)
                week += max(end_timestamp - max(begin_timestamp, week_begin), 0)
                day += max(end_timestamp - max(begin_timestamp, day_begin), 0)

                return Period(begin, end)
        else:
            def mk_period(begin: datetime, end: datetime):
                nonlocal last_update
                assert end > begin
                assert end <= datetime.now()
                assert last_update is None or last_update < begin
                last_update = end
                return Period(begin, end)

        conn: sqlite.Connection
        with sqlite.connect(db) as conn:
            cursor = conn.cursor()

            try:
                cursor.execute(
                    f"SELECT first_timestamp, last_timestamp "
                    f"FROM active_time WHERE last_timestamp > {datetime(datetime.now().year, 1, 1).timestamp()} "
                    f"ORDER BY first_timestamp"
                )
            except sqlite.OperationalError:
                res = WorkStatistics()
                res._periods = []
                return res

        res = WorkStatistics()
        res._periods = [
                mk_period(datetime.fromtimestamp(begin), datetime.fromtimestamp(end))
                for begin, end in cursor.fetchall()
        ]
        res._last_update = last_update
        res._db = db

        if cache_ymwd:
            res._cache_ymwd = True
            res._year = year
            res._month = month
            res._week = week
            res._day = day

        return res

    def period_stat(self, begin: datetime, end: Optional[datetime] = None) -> timedelta:
        """
        активное время за произвольный промежуток времени

        :param begin: начало рассматриваемого промежутка
        :param end: конец рассматриваемого промежутка
        :return: активное время
        """

        assert end is None or end > begin
        return timedelta(seconds=sum(
                min(end, it.end).timestamp() - max(begin, it.begin).timestamp()
                if end is not None
                else it.end.timestamp() - max(begin, it.begin).timestamp()
                for it in self._periods
                if it.end > begin and (end is None or it.begin < end)
        ))

    def update(self):
        """
        подгружает при необходимости новые данные из базы и обновляет изначально вычесленные значения если они были
        """

        assert self._last_update

        if self._cache_ymwd:
            today = date.today()
            if today.year != self._last_update.year:
                self._year = 0
                self._month = 0
                self._week = 0
                self._day = 0
            elif today.month != self._last_update.month:
                self._month = 0
                self._week = 0
                self._day = 0
            elif today.day != self._last_update.day:
                self._day = 0

                if today.weekday() < self._last_update.weekday() \
                        or today.day - self._last_update.day >= 7:
                    self._week = 0

            def mk_period(begin: datetime, end: datetime) -> Period:
                """
                создает промежуток времени, обновляя зарание вычисленные значения активного времени
                """

                assert end > begin

                begin_timestamp = begin.timestamp()
                end_timestamp = end.timestamp()
                assert end_timestamp < datetime.now().timestamp()
                assert self._last_update <= begin
                self._last_update = end

                self._year += max(end_timestamp - max(begin_timestamp, year_begin), 0)
                self._month += max(end_timestamp - max(begin_timestamp, month_begin), 0)
                self._week += max(end_timestamp - max(begin_timestamp, week_begin), 0)
                self._day += max(end_timestamp - max(begin_timestamp, day_begin), 0)

                return Period(begin, end)
        else:
            mk_period = Period

        conn: sqlite.Connection
        with sqlite.connect(self._db) as conn:
            cursor = conn.cursor()
            cursor.execute(
                f"SELECT first_timestamp, last_timestamp "
                f"FROM active_time WHERE last_timestamp > {self._last_update.timestamp()} "
                f"ORDER BY first_timestamp"
            )
        self._periods += [
            mk_period(max(datetime.fromtimestamp(begin), self._last_update), datetime.fromtimestamp(end))
            for begin, end in cursor.fetchall()
        ]

    @property
    def year(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._year)

        now = date.today()
        return self.period_stat(datetime(now.year, 1, 1))

    @property
    def month(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._month)

        now = date.today()
        return self.period_stat(datetime(year=now.year, month=now.month, day=1))

    @property
    def week(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._week)

        now = date.today()
        return self.period_stat(datetime(now.year, now.month, now.day) - timedelta(days=now.weekday()))

    @property
    def day(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._day)

        now = date.today()
        return self.period_stat(datetime(now.year, now.month, now.day))
