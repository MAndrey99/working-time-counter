import logging
from database import Period, new_session
from datetime import datetime, date, timedelta
from typing import *

logger = logging.getLogger('wtc.WorkStatistics')


class WorkStatistics:
    __slots__ = ('_cache_ymwd', '_year', '_month', '_week', '_day', '_last_update')

    def __init__(self):
        self._last_update: Optional[datetime] = None  # время конца последнего учтеного периода
        self._cache_ymwd: bool = False  # используется ли кэширование рассчитанного отработаного времени
        self._year: Optional[int] = None  # количество отработанного времени в году (сек)
        self._month: Optional[int] = None  # количество отработанного времени в месяце (сек)
        self._week: Optional[int] = None  # количество отработанного времени в неделе (сек)
        self._day: Optional[int] = None  # количество отработанного времени в дне (сек)

    @staticmethod
    def from_db() -> 'WorkStatistics':
        """
        создание экземпляра WorkStatistics с кжшированными данными из базы
        """
        year = 0
        month = 0
        week = 0
        day = 0
        last_update: Optional[datetime] = None
        y, m, w, d = get_ymwd_begins_timestamps()

        # кэшируем данные за день, месяц, год
        with new_session() as session:
            for period in session.query(Period) \
                    .filter(Period.end > datetime(datetime.now().year, 1, 1).timestamp()) \
                    .order_by(Period.begin).all():
                assert period.end > period.begin

                begin_timestamp = period.begin.timestamp()
                end_timestamp = period.end.timestamp()
                assert end_timestamp <= datetime.now().timestamp()
                assert last_update is None or last_update <= period.begin

                last_update = period.end
                year += max(end_timestamp - max(begin_timestamp, y), 0)
                month += max(end_timestamp - max(begin_timestamp, m), 0)
                week += max(end_timestamp - max(begin_timestamp, w), 0)
                day += max(end_timestamp - max(begin_timestamp, d), 0)

        res = WorkStatistics()
        res._last_update = last_update
        res._cache_ymwd = True
        res._year = year
        res._month = month
        res._week = week
        res._day = day

        return res

    @staticmethod
    def period_stat(p: Period) -> timedelta:
        """
        :return: активное время за указанный период
        """
        if p.end is None:
            p = Period(p.begin, datetime.now())

        assert p.end > p.begin
        with new_session() as session:
            return timedelta(seconds=sum(
                min(p.end, it.end).timestamp() - max(p.begin, it.begin).timestamp()
                if p.end is not None
                else it.end.timestamp() - max(p.begin, it.begin).timestamp()
                for it in session.query(Period)
                    .filter((Period.end > p.begin) & (p.end > Period.begin))
                    .order_by(Period.begin).all()
            ))

    def update(self):
        """
        подгружает при необходимости новые данные из базы и обновляет изначально вычесленные значения если они были
        """
        if not self._cache_ymwd:
            return

        assert self._last_update

        y, m, w, d = get_ymwd_begins_timestamps()  # получаем время начала текущего года, месяца, недели, дня
        today = datetime.fromtimestamp(d)

        # обнуляем данные о времени в прошлом году, месяце, ...
        if today.date() != self._last_update.date():
            self._day = 0

            if today.year != self._last_update.year:
                self._year = 0
                self._month = 0
            elif today.month != self._last_update.month:
                self._month = 0

            # проверяем изменилась ли неделя
            if today.timestamp() - self._last_update.timestamp() > 60*60*24*7\
                    or today.weekday() < self._last_update.weekday():
                self._week = 0

        with new_session() as session:
            for period in session.query(Period) \
                    .filter(Period.end > self._last_update) \
                    .order_by(Period.begin).all():
                period.begin = max(period.begin, self._last_update)
                begin_timestamp = period.begin.timestamp()
                end_timestamp = period.end.timestamp()
                assert end_timestamp < datetime.now().timestamp()
                assert self._last_update <= period.begin

                self._last_update = period.end
                self._year += max(end_timestamp - max(begin_timestamp, y), 0)
                self._month += max(end_timestamp - max(begin_timestamp, m), 0)
                self._week += max(end_timestamp - max(begin_timestamp, w), 0)
                self._day += max(end_timestamp - max(begin_timestamp, d), 0)

    @property
    def year(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._year)

        now = datetime.now()
        return self.period_stat(Period(datetime(now.year, 1, 1), now))

    @property
    def month(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._month)

        now = datetime.now()
        return self.period_stat(Period(datetime(year=now.year, month=now.month, day=1), now))

    @property
    def week(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._week)

        now = datetime.now()
        return self.period_stat(Period(datetime(now.year, now.month, now.day) - timedelta(days=now.weekday()), now))

    @property
    def day(self) -> timedelta:
        if self._cache_ymwd:
            return timedelta(seconds=self._day)

        now = datetime.now()
        return self.period_stat(Period(datetime(now.year, now.month, now.day), now))


def get_ymwd_begins_timestamps() -> Tuple[float, float, float, float]:
    """
    :return: кортеж со временем начала текущего года, месяца, недели, дня в секундах от начала эпохи
    """
    today = date.today()
    return datetime(today.year, 1, 1).timestamp(), \
        datetime(today.year, today.month, 1).timestamp(), \
        datetime.fromordinal((today - timedelta(today.weekday())).toordinal()).timestamp(), \
        datetime.fromordinal(today.toordinal()).timestamp()
