from pathlib import Path
from typing import Callable
import logging

from work_statistics_monitor import WorkStatisticsMonitor
import daemon

APP_ROOT: Path = Path(__file__).absolute().parent.parent
DATABASE = str(APP_ROOT / 'stats.sqlite')
LOGS_DIR = APP_ROOT / 'logs'
VERSION = 'v1-dev'
STATISTIC_UPDATE_DELAY = 10
logger: logging.Logger
main: Callable


def print_info():
    print('work time counter ' + VERSION)
    print(f'Author: MAndrey99')


def print_statistics():
    monitor = WorkStatisticsMonitor(DATABASE)
    monitor.print_statistic()


def statistic_monitor():
    from time import sleep

    with WorkStatisticsMonitor(DATABASE) as monitor:
        monitor.print_statistic()
        while True:
            sleep(STATISTIC_UPDATE_DELAY)
            monitor.update()


def init():
    """
    парсит аргументы, настраивает логгирование и инициализирует функцию main
    """

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
    stat_parser.add_argument('-f', dest='follow', action='store_true', help='переводит в режим постоянного мониторинга')

    daemon_parser = subparsers.add_parser('daemon', help='производит подсчет времени и ведет журнал')
    info_parser = subparsers.add_parser('about', help='информация о программе')

    args = parser.parse_args()

    if args.action == 'daemon':
        main = partial(daemon.start, DATABASE)  # запускает демона для записи времени активности в базу
    elif args.action == 'about':
        main = print_info  # выводит информацию о программе
    elif args.action == 'stats':
        if args.follow:
            main = statistic_monitor  # данные с автоматическим обновлением
        else:
            main = print_statistics  # просто печать данных
    else:
        main = parser.print_help  # печать инфы о передаваемых параметрах


if __name__ == '__main__':
    try:
        init()
        main()
    except KeyboardInterrupt:
        pass
    except FileNotFoundError as e:
        print(e)  # например, если не найдена бд
