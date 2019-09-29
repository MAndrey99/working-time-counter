from database import new_session, Period
from datetime import datetime
from time import sleep
import logging

logger = logging.getLogger('wtc.daemon')

MINIMUM_ACTIVE_TIME = 5 * 60  # 5 min
UPDATE_DELAY = 30  # 1 sec


def main_loop():
    begin = datetime.now()
    sleep(MINIMUM_ACTIVE_TIME)

    session = new_session()
    session.add(Period(begin, None))
    logger.info('written new entry')

    while True:
        try:
            sleep(UPDATE_DELAY)
        finally:
            session.query(Period).filter(Period.begin == begin).update({'end': datetime.now()})
            session.commit()
            logger.info('entry updated')


def start():
    try:
        logger.setLevel(logging.INFO)
        logger.info('демон запущен')
        main_loop()
    except KeyboardInterrupt:
        logger.info('демон завершил работу')
    except Exception as e:
        logger.error(f'демон завершил работу с ошибкой {e}')
