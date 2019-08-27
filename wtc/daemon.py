import sqlite3 as sqlite
from time import time, sleep
import logging

logger = logging.getLogger('wtc.daemon')

MINIMUM_ACTIVE_TIME = 5 * 60  # 5 min
UPDATE_DELAY = 60  # 1 min


def main_loop(conn: sqlite.Connection):
    begin = time()
    sleep(MINIMUM_ACTIVE_TIME)

    cursor = conn.cursor()  # при использовании conn.execute всеравно создается временный курсор
    cursor.execute(f'INSERT INTO active_time (first_timestamp) VALUES ({int(begin)})')
    logger.info('written new entry')

    while True:
        try:
            sleep(UPDATE_DELAY)
        finally:
            cursor.execute(f'UPDATE active_time SET last_timestamp={int(time())} WHERE first_timestamp={int(begin)}')
            conn.commit()
            logger.info('entry updated')


def init(conn: sqlite.Connection):
    logger.setLevel(logging.INFO)

    conn.execute('''
    CREATE TABLE IF NOT EXISTS active_time (
        first_timestamp timestamp PRIMARY KEY,
        last_timestamp timestamp DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    logger.info('демон запущен')


def start(db):
    try:
        with sqlite.connect(db) as conn:
            init(conn)
            main_loop(conn)
    except KeyboardInterrupt:
        logger.info('демон завершил работу')
    except Exception as e:
        logger.error(f'демон завершил работу с ошибкой {e}')
