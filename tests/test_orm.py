from pytest import raises
from datetime import datetime, date, timedelta
from random import randint, choice, random
from database import Period
from typing import *


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

            begin_timestamp = randint(0, 10**10)
            begin = to_rand_type(begin_timestamp)
            if type(begin) is date:
                begin_datetime = datetime.fromordinal(date.fromtimestamp(begin_timestamp).toordinal())
            else:
                begin_datetime = datetime.fromtimestamp(begin_timestamp)

            if random() < .15:
                end = None
                end_datetime = None
            else:
                end_timestamp = randint(begin_timestamp + 24 * 60 * 60, 10**10 + 24 * 60 * 60 + 1)
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
        def random_test_case():
            def date_as_string(d: Tuple[int, Optional[int], Optional[int]], error=False) -> str:
                assert d[0] > 1000
                parts = [f'{it:0>2}' for it in d if it is not None]

                if error:
                    parts[randint(0, len(parts)) - 1] = 'xx'

                if random() < .5:  # амереканский формат
                    return '.'.join(parts)
                else:  # российский формат
                    return '.'.join(reversed(parts))

            def date_to_tuple_with_transform(d: date) -> Tuple[Tuple[int, Optional[int], Optional[int]], date]:
                if random() < .15:
                    return (d.year, None, None), date(d.year, 1, 1)
                elif random() < .15:
                    return (d.year, d.month, None), date(d.year, d.month, 1)
                else:
                    return (d.year, d.month, d.day), d

            begin = date.fromtimestamp(randint(0, int(datetime.now().timestamp()) - 1))
            begin_tuple, begin = date_to_tuple_with_transform(begin)
            if random() < .2:
                # Период размером в год, месяц или день
                if begin_tuple[1] is None:
                    end = datetime(begin.year + 1, 1, 1)
                elif begin_tuple[2] is None:
                    tmp = begin.month == 12
                    end = datetime(begin.year + tmp, 1 if tmp else begin.month + 1, 1)
                else:
                    end = begin + timedelta(days=1)

                with_error = random() < .2
                return (
                    date_as_string(begin_tuple, with_error),
                    ValueError if with_error else Period(begin, end)
                )
            elif random() < .1:
                # период до now
                return date_as_string(begin_tuple) + '-now', Period(begin, None)
            elif random() < .1:
                # неправельный период из множества дат
                return '-'.join(date_as_string(begin_tuple) * randint(3, 5)), ValueError
            else:
                end = date.fromtimestamp(randint(int(datetime.now().timestamp()) - 10**9, 10**9*2))
                end_tuple, end = date_to_tuple_with_transform(end)

                first_with_error = random() < .2
                second_with_error = random() < .2

                return (
                    date_as_string(begin_tuple, first_with_error) + '-' + date_as_string(end_tuple, second_with_error),
                    Period(begin, end) if end > begin and not first_with_error and not second_with_error else ValueError
                )

        for _ in range(1000):
            arg, res = random_test_case()
            if type(res) is type and issubclass(res, Exception):
                with raises(res):
                    Period.from_string(arg)
            else:
                assert Period.from_string(arg) == res
