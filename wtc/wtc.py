import argparse
from pathlib import Path
from sys import argv, stdout
import logging

import daemon
import stats

APP_ROOT = Path(argv[0]).parent.parent
DATABASE = APP_ROOT / 'stats.sqlite'
VERSION = 'v0.1'
logger: logging.Logger


def print_info():
    print('work time counter ' + VERSION)
    print(f'Author: MAndrey99')


def print_statistics():
    statistics = stats.WorkStatistics.from_db(DATABASE)
    print(f'in this year: {statistics.year_stat().seconds / (60*60):.1f}h')
    print(f'in this month: {statistics.month_stat().seconds / (60*60):.1f}h')
    print(f'in this week: {statistics.week_stat().seconds / (60*60):.1f}h')


def main():
    parser = argparse.ArgumentParser(description='Программа для учета рабочего времени')
    subparsers = parser.add_subparsers(dest='action')

    daemon_parser = subparsers.add_parser('daemon')
    info_parser = subparsers.add_parser('about')
    stat_parser = subparsers.add_parser('stats')

    args = parser.parse_args()

    if args.action == 'daemon':
        daemon.start(DATABASE)
    elif args.action == 'about':
        print_info()
    elif args.action == 'stats':
        print_statistics()


def init():
    global logger

    formatter = logging.Formatter(
        fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%d.%m.%y %H:%M:%S'
    )

    file_handler = logging.FileHandler(filename=APP_ROOT / 'log.txt', mode='w')
    file_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setFormatter(formatter)

    logger = logging.getLogger('wtc')
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.ERROR)


if __name__ == '__main__':
    try:
        init()
        main()
    except KeyboardInterrupt:
        pass

