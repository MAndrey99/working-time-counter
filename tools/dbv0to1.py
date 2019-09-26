from sqlalchemy import *
from sqlalchemy.orm import Session as SessionType, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date
from pathlib import Path
from typing import *

Base = declarative_base()
APP_ROOT: Path = Path(__file__).absolute().parent.parent
DATABASE = 'sqlite:///' + str(APP_ROOT / 'stats.sqlite')

engine = create_engine(DATABASE)
Session = sessionmaker(bind=engine)


def ini_period(obj, begin: Union[int, float, datetime, date], end: Optional[Union[int, float, datetime, date]]):
        assert not end or end > begin

        # преобразуем btgin и end к datetime
        if type(begin) in (int, float):
            begin = datetime.fromtimestamp(begin)
        elif type(begin) is date:
            begin = datetime.fromordinal(begin.toordinal())

        if type(end) in (int, float):
            end = datetime.fromtimestamp(end)
        elif type(end) is date:
            end = datetime.fromordinal(end.toordinal())

        assert type(begin) is datetime and (end is None or type(end) is datetime)
        obj.begin = begin
        obj.end = end


class NewPeriod(Base):
    __tablename__ = 'work_periods'
    __init__ = ini_period

    begin = Column(DateTime, primary_key=True)
    end = Column(DateTime, not_null=True)


class OldPeriod(Base):
    __tablename__ = 'active_time'
    __init__ = ini_period

    first_timestamp = Column(INT, primary_key=True)
    last_timestamp = Column(INT)


def main():
    session: SessionType = Session()

    if not engine.dialect.has_table(engine, OldPeriod.__tablename__):
        print("Ошибка! Таблица активного времени не найдена!")
        return

    if engine.dialect.has_table(engine, NewPeriod.__tablename__):
        print("Ошибка! Таблица периодов уже существует!")
        return

    NewPeriod.metadata.create_all(engine)

    for it in session.query(OldPeriod).all():
        session.add(NewPeriod(it.first_timestamp, it.last_timestamp))

    session.commit()


if __name__ == '__main__':
    main()
