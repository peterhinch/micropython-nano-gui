# Simple Date classes

The official [datetime module](https://github.com/micropython/micropython-lib/tree/master/python-stdlib/datetime)
is fully featured but substantial. This `Date` class has no concept of time,
but is very compact. Dates are stored as a small int. Contrary to normal MP
practice, properties are used. This allows basic arithmetic syntax while
ensuring automatic rollover. The speed penalty of properties is unlikely to be
a factor in date operations.

The `Date` class provides basic arithmetic and comparison methods. The
`DateCal` subclass adds pretty printing and methods to assist in creating
calendars.

# Date class

The `Date` class embodies a single date value which may be modified, copied
and compared with other `Date` instances.

## Constructor

This takes a single optional arg:
 * `lt=None` By default the date is initialised from system time. To set the
 date from another time source, a valid
 [localtime/gmtime](http://docs.micropython.org/en/latest/library/time.html#time.localtime)
 tuple may be passed.

## Method

 * `now` Arg `lt=None`. Sets the instance to the current date, from system time
 or `lt` as described above.

## Writeable properties

 * `year` e.g. 2023.
 * `month` 1 == January. May be set to any number, years will roll over if
 necessary. e.g. `d.month += 15` or `d.month -= 1`.
 * `mday` Adjust day in current month. Allowed range `1..month_length`.
 * `day` Days since epoch. Note that the epoch varies with platform - the value
 may be treated as an opaque small integer. Use to adjust a date with rollover
 (`d.day += 7`) or to assign one date to another (`date2.day = date1.day`). May
 also be used to represnt a date as a small int for saving to a file.

## Read-only property

 * `wday` Day of week. 0==Monday 6==Sunday.

## Date comparisons

Python "magic methods" enable date comparisons using standard operators `<`,
`<=`, `>`, `>=`, `==`, `!=`.

# DateCal class

This adds pretty formatting and functionality to return additional information
about the current date. The added methods and properties do not change the
date value. Primarily intended for calendars.

## Constructor

This takes a single optional arg:
 * `lt=None` See `Date` constructor.

## Methods

 * `time_offset` arg `hr=6`. This returns 0 or 1, being the offset in hours of
 UK local time to UTC. By default the change occurs when the date changes at
 00:00 UTC on the last Sunday in March and October. If an hour value is passed,
 the change will occur at the correct 01:00 UTC. This method will need to be
 adapted for other geographic locations.
 * `wday_n` arg `mday=1`. Return the weekday for a given day of the month.
 * `mday_list` arg `wday`. Given a weekday, for the current month return an
 ordered list of month days matching that weekday.

## Read-only properties

 * `month_length` Length of month in days.
 * `day_str` Day of week as a string, e.g. "Wednesday".
 * `month_str` Month as a string, e.g. "August".

## Class variables

 * `days` A 7-tuple `("Monday", "Tuesday"...)`
 * `months` A 12-tuple `("January", "February",...)`

# Example usage

```python
from date import Date
d = Date()
d.month = 1  # Set to January
d.month -= 2  # Date changes to same mday in November previous year.
d.mday = 25  # Set absolute day of month
d.day += 7  # Advance date by one week. Month/year rollover is handled.
today = Date()
if d == today:  # Date comparisons
    # do something
new_date = Date()
new_date.day = d.day  # Assign d to new_date: now new_date == d.
print(d)  # Basic numeric print.
```
The DateCal class:
```python
from date import DateCal
d = DateCal()
# Correct a UK clock for DST
d.now()
hour = (hour_utc + d.time_offset(hour_utc)) % 24
print(d)  # Pretty print
x = d.wday_n(1)  # Get day of week of 1st day of month
sundays = d.mday_list(6)  # List Sundays for the month.
wday_last = d.wday_n(d.month_length)  # Weekday of last day of month
```
