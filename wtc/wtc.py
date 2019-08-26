from pathlib import Path
import logging

import daemon
import stats

APP_ROOT: Path = Path(__file__).absolute().parent.parent
DATABASE = APP_ROOT / 'stats.sqlite'
LOGS_DIR = APP_ROOT / 'logs'
VERSION = 'v0.1.1'
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
    import argparse

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
    from logging import handlers
    from sys import stdout
    global logger

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


if __name__ == '__main__':
    try:
        init()
        main()
    except KeyboardInterrupt:
        pass

