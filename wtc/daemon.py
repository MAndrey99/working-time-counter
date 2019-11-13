from database import new_session, Period
from datetime import datetime
from time import sleep, time
import logging

logger = logging.getLogger('wtc.daemon')

MINIMUM_ACTIVE_TIME = 5 * 60  # 5m
MAX_COUNTED_SLEEP = 3 * 60 * 60  # 3h
UPDATE_DELAY = 30


def main_loop() -> bool:
    """
    Главный цикл программы

    :return: True если требуется перезапуск(например, если пользователь оставил комплютер на ночь в режиме сна.
            Время в режиме сна более MAX_COUNTED_SLEEP секунд не учитывается)
    """

    begin = datetime.now()
    sleep(MINIMUM_ACTIVE_TIME)

    with new_session() as session:
        session.add(Period(begin, datetime.now()))
        last_update = time()
        logger.info('written new entry')

        while True:
            try:
                sleep(UPDATE_DELAY)
            finally:
                if last_update + MAX_COUNTED_SLEEP < time():
                    return True  # нужен перезапуск тк мы не должны учитывать длительный сон

                session.query(Period).filter(Period.begin == begin).update({'end': datetime.now()})
                last_update = time()
                session.commit()
                logger.info('entry updated')


def start():
    try:
        logger.setLevel(logging.INFO)
        logger.info('демон запущен')
        while main_loop():
            logger.info('restarting the main loop')
    except KeyboardInterrupt:
        logger.info('демон завершил работу')
    except Exception as e:
        logger.error(f'демон завершил работу с ошибкой {e}')
