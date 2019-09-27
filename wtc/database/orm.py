from sqlalchemy import *
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as SessionType, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date
from typing import *

Base = declarative_base()
Session: Optional[SessionType]
engine: Optional[Engine] = None


class Period(Base):
    __tablename__ = 'work_periods'

    begin = Column(DateTime, primary_key=True)
    end = Column(DateTime)

    def __init__(self, begin: Union[int, float, datetime, date], end: Optional[Union[int, float, datetime, date]]):
        assert not end or end > begin

        if type(begin) in (int, float):
            begin = datetime.fromtimestamp(begin)

        if type(end) in (int, float):
            end = datetime.fromtimestamp(end)

        self.begin = begin
        self.end = end


def init(database_url: str, *, check_exists=True):
    global engine, Session
    engine = create_engine(database_url)

    if check_exists:
        try:
            assert Period.__tablename__ in MetaData(engine, reflect=True).tables
        except OperationalError:
            raise ConnectionError("невозмбжно подключиться к базе данных")

    Session = sessionmaker(bind=engine)


def create_tables():
    """Создает не существующие таблицы"""
    Base.metadata.create_all(engine)


def new_session() -> SessionType:
    if Session is not None:
        return Session()
    else:
        raise ValueError("orm не инициализарована")
