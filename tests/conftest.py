import datetime


class Datetime(datetime.datetime):
    @classmethod
    def now(cls, tz=None):
        return cls.fromtimestamp(1567633936)


class Date(datetime.date):
    @classmethod
    def today(cls):
        return cls.fromtimestamp(1567633936)


datetime.datetime = Datetime
datetime.date = Date
