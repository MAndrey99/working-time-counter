import curses
from typing import *
from dataclasses import dataclass
from work_statistics import WorkStatistics


@dataclass(order=True)
class WordPosition:
    y: int
    x: int

    def __iter__(self):
        return iter((self.y, self.x))


class WorkStatisticsMonitor:
    __slots__ = ('_stats', '_scr', '_template')

    def __init__(self):
        self._stats = WorkStatistics.from_db()
        self._template = \
            'в этом году: {year_hours}h\n' \
            'в этом месяце: {month_hours}h\n' \
            'на этой неделе: {week_hours}h\n' \
            'сегодня: {day_hours}h'
        self._scr = None

    def __enter__(self) -> 'WorkStatisticsMonitor':
        self._scr: curses = curses.initscr()
        curses.noecho()
        curses.curs_set(False)  # делаем курсор невидимым
        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb):
        curses.endwin()

    def print_statistic(self):
        if self._scr:
            self._draw()
        else:
            print(self._template.format(**self._work_statistics_dict()))

    def update(self):
        """
        Обновить данные на мониторе в соответствие с новыцми данными в бд
        """
        self._stats.update()
        self._draw()

    def _draw(self):
        for n, line in enumerate(self._template.format(**self._work_statistics_dict()).split('\n')):
            self._scr.addstr(n, 0, line)
        self._scr.refresh()
        self._scr.clear()

    def _work_statistics_dict(self) -> Dict[str, str]:
        return {
            'year_hours': f'{self._stats.year.total_seconds() / (60*60):.1f}',
            'month_hours': f'{self._stats.month.total_seconds() / (60*60):.1f}',
            'week_hours': f'{self._stats.week.total_seconds() / (60*60):.1f}',
            'day_hours': f'{self._stats.day.total_seconds() / (60*60):.1f}'
        }
