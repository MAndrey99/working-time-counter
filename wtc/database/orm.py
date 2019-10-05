import re
from sqlalchemy import *
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session as SessionType, sessionmaker
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime, date, timedelta
from typing import *

Base = declarative_base()
Session: Optional[SessionType]
engine: Optional[Engine] = None


class Period(Base):
    __tablename__ = 'work_periods'

    begin = Column(DateTime, primary_key=True)
    end = Column(DateTime)

    def __init__(self, begin: Union[int, float, datetime, date], end: Optional[Union[int, float, datetime, date]] = None):
        if type(begin) in (int, float):
            begin = datetime.fromtimestamp(begin)
        else:
            if not hasattr(begin, 'timestamp'):
                assert hasattr(begin, 'toordinal')
                begin = datetime.fromordinal(begin.toordinal())

        if type(end) in (int, float):
            end = datetime.fromtimestamp(end)
        else:
            if end:
                if not hasattr(end, 'timestamp'):
                    assert hasattr(end, 'toordinal')
                    end = datetime.fromordinal(end.toordinal())

                assert end > begin

        self.begin = begin
        self.end = end

    def __repr__(self):
        end = self.end.strftime('%Y.%m.%d %H:%M:%S') if self.end else 'now'
        return f'{self.begin.strftime("%Y.%m.%d %H:%M:%S")} - {end}'

    def __eq__(self, other: 'Period'):
        return self.begin == other.begin and self.end == other.end

    @staticmethod
    def from_string(s: str) -> 'Period':
        assert s

        dates: List[Union[str, datetime]] = s.split('-')
        if len(dates) > 2:
            raise ValueError('неверный формат периода')

        date_reg = re.compile(r'(?:(?:(?P<day>\d{2})\.)?(?P<month>\d{2})\.)?(?P<year>\d{4})')
        us_like_date_reg = re.compile(r'(?P<year>\d{4})?(?:\.(?P<month>\d{2})(?:\.(?P<day>\d{2}))?)?')

        def parse_date(date_string: str) -> Optional[Tuple[datetime, int]]:
            """
            :param date_string: строка с единственной датой
            :param op: add если надо взять следующий день, sub, если предыдущий, по-умолчанию точно указаный
            :return: представление указаной даты в виде обьекта datetime и "ранг" даты, равный 0, 1(если день не указан)
            или 2(если месяц не указан)
            """

            if date_string == 'now':
                return datetime.now(), 0

            m = re.fullmatch(date_reg, date_string)
            if not m:
                m = re.fullmatch(us_like_date_reg, date_string)
                if not m:
                    return None

            return datetime(
                int(m.group('year')),
                int(m.group('month')) if m.group('month') else 1,
                int(m.group('day')) if m.group('day') else 1
            ), 0 if m.group('day') is not None else (1 if m.group('month') is not None else 2)

        if len(dates) == 2:
            dates = [it[0] for it in map(parse_date, dates)]
        else:
            dates[0], rang = parse_date(dates[0])
            if rang == 0:
                dates.append(dates[0] + timedelta(days=1))
            elif rang == 1:
                tmp = dates[0].month == 12
                dates.append(datetime(dates[0].year + tmp, 1 if tmp else dates[0].month + 1, 1))
            elif rang == 2:
                dates.append(datetime(dates[0].year + 1, 1, 1))

        if not all(dates):
            raise ValueError('неверный формат даты')

        if len(dates) == 2 and dates[1] < dates[0]:
            raise ValueError('дата начала анализируемого промежутка времени обязана быть меньше даты конца')

        return Period(dates[0], dates[1] if len(dates) == 2 else None)


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
