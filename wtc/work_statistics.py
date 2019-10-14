import logging
from database import Period, new_session
from datetime import datetime, date, timedelta
from typing import *

logger = logging.getLogger('wtc.WorkStatistics')


class WorkStatistics:
    __slots__ = ('_periods', '_cache_ymwd', '_year', '_month', '_week', '_day', '_last_update')

    def __init__(self):
        self._last_update: Optional[datetime] = None  # время последнего обновления данных из бд
        self._periods: Optional[List[Period]] = None  # список периодов работы за максимальный рассматриваемый срок
        self._cache_ymwd: bool = False  # используется ли кэширование рассчитанного отработаного времени
        self._year: Optional[int] = None  # количество отработанного времени в году (сек)
        self._month: Optional[int] = None  # количество отработанного времени в месяце (сек)
        self._week: Optional[int] = None  # количество отработанного времени в неделе (сек)
        self._day: Optional[int] = None  # количество отработанного времени в дне (сек)

    @staticmethod
    def from_db(*, cache_ymwd=True, cache_data=False) -> 'WorkStatistics':
        """
        загрузка данных из базы и создание экземпляра WorkStatistics

        :param db: имя/путь базы
        :param cache_ymwd: требуется ли кэшировать статистику за год, месяц, неделю, день
        :param cache_data: требуется ли кэшировать рабочие промежутки за последний год(позволяет смотреть статистику за
        произвольный промежуток времени без обращения к бд)
        :return: WorkStatistics со считанной из бд информацией
        """

        mk_period: Callable[[datetime, datetime], Period]
        year = 0
        month = 0
        week = 0
        day = 0
        last_update: Optional[datetime] = None

        if cache_ymwd:
            y, m, w, d = get_ymwd_begins_timestamps()

            def mk_period(begin: datetime, end: datetime):
                nonlocal year, month, week, day, last_update
                assert end > begin

                begin_timestamp = begin.timestamp()
                end_timestamp = end.timestamp()
                assert end_timestamp <= datetime.now().timestamp()
                assert last_update is None or last_update <= begin
                last_update = end

                year += max(end_timestamp - max(begin_timestamp, y), 0)
                month += max(end_timestamp - max(begin_timestamp, m), 0)
                week += max(end_timestamp - max(begin_timestamp, w), 0)
                day += max(end_timestamp - max(begin_timestamp, d), 0)

                return Period(begin, end)
        else:
            def mk_period(begin: datetime, end: datetime):
                nonlocal last_update
                assert end > begin
                assert end <= datetime.now()
                assert last_update is None or last_update < begin
                last_update = end
                return Period(begin, end)

        res = WorkStatistics()
        with new_session() as session:
            if cache_data:
                res._periods = []

            for period in session.query(Period) \
                    .filter(Period.end > datetime(datetime.now().year, 1, 1).timestamp()) \
                    .order_by(Period.begin).all():
                period = mk_period(period.begin, period.end)  # для возможности кэшировать день, месяц, год
                if cache_data:
                    res._periods.append(period)

        res._last_update = last_update

        if cache_ymwd:
            res._cache_ymwd = True
            res._year = year
            res._month = month
            res._week = week
            res._day = day

        return res

    def period_stat(self, p: Period) -> timedelta:
        """
        активное время за произвольный промежуток времени

        :param p: промежуток в котором будет считаться активное время
        :return: активное время
        """

        if p.end is None:
            p = Period(p.begin, datetime.now())

        assert p.end > p.begin

        if self._periods is not None:
            return timedelta(seconds=sum(
                min(p.end, it.end).timestamp() - max(p.begin, it.begin).timestamp()
                if p.end is not None
                else it.end.timestamp() - max(p.begin, it.begin).timestamp()
                for it in self._periods
                if it.end > p.begin and it.begin < p.end
            ))
        else:
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

        assert self._last_update

        if self._cache_ymwd:
            y, m, w, d = get_ymwd_begins_timestamps()
            today = datetime.fromtimestamp(d)

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

                self._year += max(end_timestamp - max(begin_timestamp, y), 0)
                self._month += max(end_timestamp - max(begin_timestamp, m), 0)
                self._week += max(end_timestamp - max(begin_timestamp, w), 0)
                self._day += max(end_timestamp - max(begin_timestamp, d), 0)

                return Period(begin, end)
        else:
            mk_period = Period

        with new_session() as session:
            for period in session.query(Period) \
                    .filter(Period.end > self._last_update) \
                    .order_by(Period.begin).all():
                period = mk_period(max(period.begin, self._last_update), period.end)
                if self._periods is not None:
                    self._periods.append(period)

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
    today = date.today()
    return datetime(today.year, 1, 1).timestamp(), \
        datetime(today.year, today.month, 1).timestamp(), \
        datetime.fromordinal((today - timedelta(today.weekday())).toordinal()).timestamp(), \
        datetime.fromordinal(today.toordinal()).timestamp()
