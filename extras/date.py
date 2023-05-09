# date.py Minimal Date class for micropython

# Released under the MIT License (MIT). See LICENSE.
# Copyright (c) 2023 Peter Hinch

from time import mktime, localtime

_SECS_PER_DAY = const(86400)
def leap(year):
    return bool((not year % 4) ^ (not year % 100))

class Date:

    def __init__(self, lt=None):
        self.callback = lambda : None  # No callback until set
        self.now(lt)

    def now(self, lt=None):
        self._lt = list(localtime()) if lt is None else list(lt)
        self._update()

    def _update(self, ltmod=True):  # If ltmod is False ._cur has been changed
        if ltmod:  # Otherwise ._lt has been modified
            self._lt[3] = 6
            self._cur = mktime(self._lt) // _SECS_PER_DAY
        self._lt = list(localtime(self._cur * _SECS_PER_DAY))
        self.callback()

    def _mlen(self, d=bytearray((31, 0, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31))):
        days = d[self._lt[1] - 1]
        return days if days else (29 if leap(self._lt[0]) else 28)

    @property
    def year(self):
        return self._lt[0]

    @year.setter
    def year(self, v):
        if  self.mday == 29 and self.month == 2 and not leap(v):
            self.mday = 28  # Ensure it doesn't skip a month
        self._lt[0] = v
        self._update()

    @property
    def month(self):
        return self._lt[1]

    # Can write d.month = 4 or d.month += 15
    @month.setter
    def month(self, v):
        y, m = divmod(v - 1, 12)
        self._lt[0] += y
        self._lt[1] = m + 1
        self._lt[2] = min(self._lt[2], self._mlen())
        self._update()

    @property
    def mday(self):
        return self._lt[2]

    @mday.setter
    def mday(self, v):
        if not 0 < v <= self._mlen():
            raise ValueError(f"mday {v} is out of range")
        self._lt[2] = v
        self._update()

    @property
    def day(self):  # Days since epoch.
        return self._cur

    @day.setter
    def day(self, v):  # Usage: d.day += 7 or date_1.day = d.day.
        self._cur = v
        self._update(False)  # Flag _cur change

    # Read-only properties

    @property
    def wday(self):
        return self._lt[6]

    # Date comparisons

    def __lt__(self, other):
        return self.day < other.day

    def __le__(self, other):
        return self.day <= other.day

    def __eq__(self, other):
        return self.day == other.day

    def __ne__(self, other):
        return self.day != other.day

    def __gt__(self, other):
        return self.day > other.day

    def __ge__(self, other):
        return self.day >= other.day

    def __str__(self):
        return f"{self.year}/{self.month}/{self.mday}"


class DateCal(Date):
    days = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")
    months = (
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    )

    def __init__(self, lt=None):
        super().__init__(lt)

    @property
    def month_length(self):
        return self._mlen()

    @property
    def day_str(self):
        return self.days[self.wday]

    @property
    def month_str(self):
        return self.months[self.month - 1]

    def wday_n(self, mday=1):
        return (self._lt[6] - self._lt[2] + mday) % 7

    def mday_list(self, wday):
        ml = self._mlen()  # 1 + ((wday - wday1) % 7)
        d0 = 1 + ((wday - (self._lt[6] - self._lt[2] + 1)) % 7)
        return [d for d in range(d0, ml + 1, 7)]

    # Optional: return UK DST offset in hours. Can pass hr to ensure that time change occurs
    # at 1am UTC otherwise it occurs on date change (0:0 UTC)
    # offs is offset by month
    def time_offset(self, hr=6, offs=bytearray((0, 0, 3, 1, 1, 1, 1, 1, 1, 10, 0, 0))):
        ml = self._mlen()
        wdayld = self.wday_n(ml)  # Weekday of last day of month
        mday_sun = self.mday_list(6)[-1]  # Month day of last Sunday
        m = offs[self._lt[1] - 1]
        if m < 3:
            return m  # Deduce time offset from month alone
        return int(
            ((self._lt[2] < mday_sun) or (self._lt[2] == mday_sun and hr <= 1)) ^ (m == 3)
        )  # Months where offset changes

    def __str__(self):
        return f"{self.day_str} {self.mday} {self.month_str} {self.year}"
