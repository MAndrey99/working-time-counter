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


class WordStatisticsMonitor:
    __slots__ = ('_stats', '_scr', '_template', '_display_positions')

    def __init__(self, db: str):
        self._stats = WorkStatistics.from_db(db)
        # при изменении шаблона не забыть изменить _display_positions в __enter__!
        self._template = \
            'в этом году: {year_hours}h\n' \
            'в этом месяце: {month_hours}h\n' \
            'на этой неделе: {week_hours}h\n' \
            'егодня: {day_hours}h'

    def __enter__(self):
        self._display_positions = {
            'year_hours': WordPosition(0, 13),
            'month_hours': WordPosition(1, 15),
            'week_hours': WordPosition(2, 16),
            'day_hours': WordPosition(3, 8)
        }
        self._scr: curses = curses.initscr()
        curses.noecho()
        curses.curs_set(False)  # делаем курсор невидимым

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb):
        curses.endwin()

    def print(self):
        print(self._template.format(**self.work_statistics_dict()))

    def update(self):
        self._stats.update()

        for k, v in self.work_statistics_dict().items():
            self._scr.addstr(*self._display_positions[k], v)

        self._scr.refresh()

    def work_statistics_dict(self) -> Dict[str, str]:
        return {
            'year_hours': f'{self._stats.year.seconds / (60*60):.1f}',
            'month_hours': f'{self._stats.year.seconds / (60*60):.1f}',
            'week_hours': f'{self._stats.year.seconds / (60*60):.1f}',
            'day_hours': f'{self._stats.year.seconds / (60*60):.1f}'
        }
