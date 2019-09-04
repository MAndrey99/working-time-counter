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
        # TODO: автоматическое вычисление позиций
        self._template = \
            'в этом году: {year_hours}h\n' \
            'в этом месяце: {month_hours}h\n' \
            'на этой неделе: {week_hours}h\n' \
            'сегодня: {day_hours}h'

    def __enter__(self) -> 'WordStatisticsMonitor':
        self._display_positions = {
            'year_hours': WordPosition(0, 13),
            'month_hours': WordPosition(1, 15),
            'week_hours': WordPosition(2, 16),
            'day_hours': WordPosition(3, 8)
        }
        self._scr: curses = curses.initscr()
        curses.noecho()
        curses.curs_set(False)  # делаем курсор невидимым

        return self

    def __exit__(self, exc_type: type, exc_val: Exception, exc_tb):
        curses.endwin()

    def print_statistic(self):
        # TODO: добавить проверку на режим работы: с curses так лучше не выводить
        print(self._template.format(**self._work_statistics_dict()))

    def update(self):
        """
        Обновить данные на мониторе в соответствие с новыцми данными в бд
        """

        self._stats.update()

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
