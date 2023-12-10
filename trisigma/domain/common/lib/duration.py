from datetime import datetime, timedelta, date
import math

SECOND = 1
MINUTE = 60
HOUR = 3600
DAY = 86400
WEEK = 604800
MONTH = 2592000
YEAR = 31536000

def next_interval(timestamp, mins, offset=0):
    intv_sec = (mins*60)
    next_ts = (timestamp // intv_sec + 1) * intv_sec
    seconds_left = next_ts - timestamp - offset
    return seconds_left

class BadIntervalError (Exception):
   pass

def parse_duration(rng) -> int:
    """Converts a string interval into int seconds, eg. "1m" --> 60, "2d" --> 172800

    :param rng: interval
    :type rng: string
    """
    rng = rng.lower()
    units = {'s': (['s', 'sec', 'second', 'seconds'], 1),
            'm': (['m', 'min', 'minute', 'minutes'], 60),
            'h': (['h', 'hour', 'hours'], 3600),
            'd': (['d', 'day', 'days'], 86400),
            'w': (['w', 'week', 'weeks'], 604800),
            'y': (['y', 'year', 'years'], 31536000)}
    unit = ''.join(list(filter(lambda c: c.isalpha(), rng)))
    coef = int(''.join(list(filter(lambda c: c.isnumeric(), rng))))
    for v in units.values():
        if unit in v[0]:
            result = v[1] * coef
            return result
    raise BadIntervalError(f"Bad interval: {rng}")

def find_best_timeunit(seconds) -> int:
    durations = (SECOND, MINUTE, HOUR,
                 DAY, WEEK, MONTH, YEAR)
    divisor = 1
    for duration in durations:
        if seconds % duration == 0:
            divisor = duration
    return divisor



def parse_duration_split(rng) -> tuple:
    """Converts a string interval into a tuple where the 1st index represents the coefficient, and the 2nd index is the time unit represented in seconds
        eg. "1m" --> (1, 60)
            "2d" --> (2, 172800)

    :param rng: interval
    :type rng: string
    """
    rng = rng.lower()
    units = {'s': (['s', 'sec', 'second', 'seconds'], 1),
             'm': (['m', 'min', 'minute', 'minutes'], 60),
             'h': (['h', 'hour', 'hours'], 3600),
             'd': (['d', 'day', 'days'], 86400),
             'w': (['w', 'week', 'weeks'], 604800),
             'y': (['y', 'year', 'years'], 31536000)}
    unit = ''.join(list(filter(lambda c: c.isalpha(), rng)))
    coef = int(''.join(list(filter(lambda c: c.isnumeric(), rng))))
    for v in units.values():
        if unit in v[0]:
            return (coef, v[1])
    raise BadIntervalError(f"Bad interval: {rng}")


TIMEUNITS = {
    SECOND: 's',
    MINUTE: 'm',
    HOUR: 'h',
    DAY: 'd',
    WEEK: 'w',
    YEAR: 'y'
}

class Interval:

    seconds: int
    coef: int
    unit: int

    def __init__(
        self,
        interval
    ):
        self.seconds = convert_duration(interval)
        self.unit = find_best_timeunit(self.seconds)
        self.coef = int(self.seconds / self.unit)

    def __str__(self):
        return self.strf("{coef}{unit}")

    def __repr__(self):
        return f"Interval({self.__str__()})"

    def __int__(self):
        return self.seconds

    def __float__(self):
        return float(self.seconds)

    def floor(self, epoch: int):
        floored = epoch - (epoch % self.seconds)
        return floored

    @staticmethod
    def parse(duration: str):
        return Interval(duration)

    def strf(self, fmt, units={}):
        unit = units.get(self.unit, TIMEUNITS[self.unit])
        coef = self.coef
        return fmt.format(coef=coef, unit=unit)

    def to_pandas_str(self):
        units = {
            MINUTE: "T",
            HOUR: "H",
            DAY: "D",
            WEEK: "W",
            YEAR: "Y"
        }
        intv = self.strf("{coef}{unit}", units)
        return intv

    def copy(self):
        return Interval(self.seconds)

def convert_duration(dur) -> int:
    if isinstance(dur, timedelta):
        return int(dur.total_seconds())
    elif isinstance(dur, int) or isinstance(dur, float):
        return int(dur)
    elif isinstance(dur, str):
        return parse_duration(dur)
    else:
        raise TypeError(f"Cannot convert {dur} to duration")

class TimeSpan:

    start: datetime
    end: datetime
    duration: float

    def __init__(self, start, end = None):
        self.start = convert_datetype(start)
        self.end = convert_datetype(end)
        self.duration = (self.end - self.start).total_seconds()

    def to_epoch(self):
        return int(self.start.timestamp()), int(self.end.timestamp())

    def to_dates(self):
        start = self.start.date()
        end = self.end.date()
        return start, end

    def to_datetime(self):
        return self.start, self.end

    def copy(self):
        return TimeSpan(self.start, self.end)

    def __contains__(self, other):
        dt = convert_datetype(other)
        return self.start <= dt <= self.end

    def __int__(self):
        return int(self.duration)

    def __float__(self):
        return float(self.duration)


def convert_datetype(dt) -> datetime:
    if dt is None:
        return datetime.now()
    elif isinstance(dt, datetime):
        return dt
    elif isinstance(dt, date):
        return datetime.combine(dt, datetime.min.time())
    elif isinstance(dt, int) or isinstance(dt, float):
        if int(math.log10(dt)) == 9:
            return datetime.fromtimestamp(dt)
        elif int(math.log10(dt)) == 12:
            return datetime.fromtimestamp(dt / 1000)
        else:
            raise Exception("Invalid timestamp")
    elif isinstance(dt, str):
        return datetime.fromisoformat(dt)
    else:
        raise Exception("Invalid Datetype")




def floor(date, interval, delta=None) -> datetime:
    """Makes a floor rounding to the given date.
        eg. date = <2022-10-28:23-53-13>, interval = "15m" --> <2022-10-28:23-45-00>
            date = <2022-10-28:23-53-13>, interval = "1d" --> <2022-10-28:00-00-00>

    :param date: the date that will be rounded.
    :type date: <datetime.datetime> or <int> (as a timestamp)
    :param interval: the interval that will be used to round the date.
    :type interval: <str>
    :param delta: (Optional) adds offset to the rounding. eg: interval="1w", delta=timedelta(days=2) will round to the last Wednesday, instead of Monday.
    :type delta: <datetime.timedelta>
    """
    if delta != None:
        delta = delta.total_seconds()
    else:
        delta = 0
    if not isinstance(date, (int, float)):
        date = date.timestamp()
    units = {'w': (604800, 345600), 'd': (86400, 0),
                'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
    freq = int(''.join([i for i in interval if i.isdigit()]))
    unit = ''.join([i for i in interval if i.isalpha()])
    coef = units[unit][0] * freq
    delt = units[unit][1] + delta

    result = (date - delt) - ((date - delt) % coef) + delt
    return datetime.fromtimestamp(int(result))


def ceil(date, interval, delta=None) -> datetime:
    """Makes a ceil rounding to the given date.
        eg. date = <2022-10-28:23-53-13>, interval = "15m" --> <2022-10-29:00-00-00>
            date = <2022-10-28:23-53-13>, interval = "2d" --> <2022-10-30:00-00-00>

    :param date: the date that will be rounded.
    :type date: <datetime.datetime> or <int> (as a timestamp)
    :param interval: the interval that will be used to round the date.
    :type interval: <str>
    :param delta: (Optional) adds offset to the rounding. eg: interval="1w", delta=timedelta(days=2) will round to the next Wednesday, instead of Monday.
    :type delta: <datetime.timedelta>
    """

    if delta != None:
        delta = delta.total_seconds()
    else:
        delta = 0
    if not isinstance(date, (int, float)):
        date = date.timestamp()
    units = {'w': (604800, 345600), 'd': (86400, 0),
             'h': (3600, 0), 'm': (60, 0), 's': (1, 0)}
    freq = int(''.join([i for i in interval if i.isdigit()]))
    unit = ''.join([i for i in interval if i.isalpha()])
    coef = units[unit][0] * freq
    delt = units[unit][1] + delta

    result = (date - delt) - ((date - delt) % coef) + delt + coef
    return datetime.fromtimestamp(int(result))

