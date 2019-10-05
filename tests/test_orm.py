from pytest import fail
from datetime import datetime, date
from random import randint, choice, random
from database import Period


class TestPeriod:
    def test_init(self):
        # Period должен самостоятельно переводить аргументы конструктора в формат datetime
        arg_types = (int, float, date, datetime)

        def random_test_case():
            def to_rand_type(d: int):
                t = choice(arg_types)
                if t is float:
                    return float(d)
                elif t in (date, datetime):
                    return t.fromtimestamp(d)
                else:
                    assert t is int
                    return d

            begin_timestamp = randint(0, 10*10)
            begin = to_rand_type(begin_timestamp)
            if type(begin) is date:
                begin_datetime = datetime.fromordinal(date.fromtimestamp(begin_timestamp).toordinal())
            else:
                begin_datetime = datetime.fromtimestamp(begin_timestamp)

            if random() < .15:
                end = None
                end_datetime = None
            else:
                end_timestamp = randint(begin_timestamp + 24 * 60 * 60, 10*10 + 24 * 60 * 60)
                end = to_rand_type(end_timestamp)
                if type(end) is date:
                    end_datetime = datetime.fromordinal(date.fromtimestamp(end_timestamp).toordinal())
                else:
                    end_datetime = datetime.fromtimestamp(end_timestamp)

            return (begin, end), (begin_datetime, end_datetime)

        for _ in range(100):
            args, res = random_test_case()
            t = Period(*args)
            assert (t.begin, t.end) == res

    def test_from_string(self):
        fail()  # TODO
