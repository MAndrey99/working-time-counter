from pathlib import Path
from typing import Callable
import logging

from work_statistics_monitor import WorkStatisticsMonitor
import daemon

APP_ROOT: Path = Path(__file__).absolute().parent.parent
DATABASE = 'sqlite:///' + str(APP_ROOT / 'stats.sqlite')
CONFIGFILE = APP_ROOT / 'config.ini'
LOGS_DIR = APP_ROOT / 'logs'
VERSION = 'v1.1'
STATISTIC_UPDATE_DELAY = 10
logger: logging.Logger
main: Callable


def print_info():
    """
    Вывод основной информации о программе
    """
    print('work time counter ' + VERSION)
    print('Author: MAndrey99')


def print_statistics():
    """
    Вывод статистики за год, месяц, неделю, день
    """
    monitor = WorkStatisticsMonitor()
    monitor.print_statistic()


def statistic_monitor():
    """
    Вывод статистики за год, месяц, неделю, день с автоматическим обновлением раз в STATISTIC_UPDATE_DELAY секунд
    """
    from time import sleep

    with WorkStatisticsMonitor() as monitor:
        monitor.print_statistic()
        while True:
            sleep(STATISTIC_UPDATE_DELAY)
            monitor.update()


def init_logging():
    """
    Настраевает логгирования
    """

    from logging import handlers
    from sys import stdout
    global logger

    if not LOGS_DIR.is_dir():
        LOGS_DIR.mkdir()

    formatter = logging.Formatter(
        fmt='%(asctime)s [%(name)s] %(levelname)s: %(message)s',
        datefmt='%d.%m.%y %H:%M:%S'
    )

    file_handler = handlers.RotatingFileHandler(LOGS_DIR / 'log', maxBytes=1024 ** 2, backupCount=1,
                                                encoding="utf-8")
    file_handler.setFormatter(formatter)

    stdout_handler = logging.StreamHandler(stdout)
    stdout_handler.setFormatter(logging.Formatter(
        fmt='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%H:%M:%S'
    ))

    logger = logging.getLogger('wtc')
    logger.addHandler(stdout_handler)
    logger.addHandler(file_handler)
    logger.setLevel(logging.ERROR)


def parse_args_and_init_main():
    """
    Парсит аргументы командной строки и инициализирует функцию main
    """

    import argparse
    from database import Period, create_tables, init as init_orm
    global main

    parser = argparse.ArgumentParser(description='Программа для учета рабочего времени')
    subparsers = parser.add_subparsers(dest='action')

    stat_parser = subparsers.add_parser('stat', help='выводит подсчитаное время')
    stat_parser.add_argument('-f', dest='follow', action='store_true',
                             help='переводит в режим постоянного мониторинга')
    stat_parser.add_argument(dest='period', type=Period.from_string, default=None, nargs='?')

    subparsers.add_parser('daemon', help='производит подсчет времени и ведет журнал')
    subparsers.add_parser('about', help='информация о программе')

    args = parser.parse_args()

    if args.action == 'daemon':
        main = daemon.start  # запускает демона для записи времени активности в базу
        init_orm(DATABASE, check_exists=False)
        create_tables()
    elif args.action == 'about':
        main = print_info  # выводит информацию о программе
    elif args.action == 'stat':
        if args.period:
            def print_period_statistics():
                from work_statistics import WorkStatistics
                print(f'{WorkStatistics.period_stat(args.period).total_seconds() / 3600:.1f}h')

            main = print_period_statistics
            if args.follow:
                print('отображение в реальном времени для временных промежутков пока недоступно(')
        else:
            if args.follow:
                main = statistic_monitor  # данные с автоматическим обновлением
            else:
                main = print_statistics  # просто печать данных

        init_orm(DATABASE)
    else:
        main = parser.print_help  # печать инфы о передаваемых параметрах


def apply_configfile():
    from configparser import ConfigParser
    global STATISTIC_UPDATE_DELAY

    config = ConfigParser()
    config.read(CONFIGFILE)

    # client
    client_config = config['client']
    STATISTIC_UPDATE_DELAY = client_config.getfloat('statistic_update_delay', STATISTIC_UPDATE_DELAY)

    # daemon
    daemon_config = config['daemon']
    daemon.MINIMUM_ACTIVE_TIME = daemon_config.getfloat('minimum_active_time', daemon.MINIMUM_ACTIVE_TIME)
    daemon.MAX_COUNTED_SLEEP = daemon_config.getfloat('max_counted_sleep', daemon.MAX_COUNTED_SLEEP)
    daemon.UPDATE_DELAY = daemon_config.getfloat('update_delay', daemon.UPDATE_DELAY)


def create_default_configfile():
    with CONFIGFILE.open('w') as f:
        f.write(f'''\
# время указывается в секундах

[daemon]
# минимальное учитываение время работы компьютера
minimum_active_time = {daemon.MINIMUM_ACTIVE_TIME}

# максимальное засчитываемое время в режиме сна
max_counted_sleep = {daemon.MAX_COUNTED_SLEEP}

# пауза после каждого обновления статистики
update_delay = {daemon.UPDATE_DELAY}

[client]
# раз в какой промежуток времени будет обновляться информация в интерактивном режиме
statistic_update_delay = {STATISTIC_UPDATE_DELAY}
''')


def init():
    init_logging()
    parse_args_and_init_main()

    if CONFIGFILE.is_file():
        apply_configfile()
    else:
        create_default_configfile()


if __name__ == '__main__':
    try:
        init()
        main()
    except KeyboardInterrupt:
        pass
    except FileNotFoundError as e:  # например, если не найдена бд
        logger.error(e)
