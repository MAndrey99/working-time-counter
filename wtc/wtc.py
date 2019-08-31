from pathlib import Path
from typing import Callable
import logging

from work_statistics import WorkStatistics
import daemon

APP_ROOT: Path = Path(__file__).absolute().parent.parent
DATABASE = str(APP_ROOT / 'stats.sqlite')
LOGS_DIR = APP_ROOT / 'logs'
VERSION = 'v0.3'
logger: logging.Logger
main: Callable


def print_info():
    print('work time counter ' + VERSION)
    print(f'Author: MAndrey99')


def print_statistics():
    statistics = WorkStatistics.from_db(DATABASE)
    print(f'в этом году: {statistics.year.seconds / (60*60):.1f}h')
    print(f'в этом месяце: {statistics.month.seconds / (60*60):.1f}h')
    print(f'на этой неделе: {statistics.week.seconds / (60*60):.1f}h')
    print(f'сегодня: {statistics.day.seconds / (60*60):.1f}h')


def init():
    import argparse
    from logging import handlers
    from functools import partial
    from sys import stdout
    global logger, main

    # настраиваем логгирование
    if not LOGS_DIR.is_dir():
        LOGS_DIR.mkdir()

    formatter = logging.Formatter(
        fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%d.%m.%y %H:%M:%S'
    )

    file_handler = handlers.RotatingFileHandler(LOGS_DIR / 'log', maxBytes=1024**2, backupCount=1, encoding="utf-8")
    file_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setFormatter(formatter)

    logger = logging.getLogger('wtc')
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.ERROR)

    # парсим аргументы и инициализируем функцию main
    parser = argparse.ArgumentParser(description='Программа для учета рабочего времени')
    subparsers = parser.add_subparsers(dest='action')

    stat_parser = subparsers.add_parser('stats', help='выводит подсчитаное время')
    daemon_parser = subparsers.add_parser('daemon', help='производит подсчет времени и ведет журнал')
    info_parser = subparsers.add_parser('about', help='информация о программе')

    args = parser.parse_args()

    if args.action == 'daemon':
        main = partial(daemon.start, DATABASE)
    elif args.action == 'about':
        main = print_info
    elif args.action == 'stats':
        main = print_statistics
    else:
        main = parser.print_help


if __name__ == '__main__':
    try:
        init()
        main()
    except KeyboardInterrupt:
        pass
