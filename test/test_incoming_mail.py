#!/usr/bin/python

import unittest
from incoming_mail import CreateEventHandler


class FormatDate(unittest.TestCase):
    valid = ( # PM:
              ("2011-02-11T15:00:00.000-07:00", "Fri Feb 11 03:00 PM"),

              # AM:
              ("2011-06-11T10:08:12.000-06:00", "Sat Jun 11 10:08 AM"),

              # Timezone should be ignored:
              ("2011-06-11T15:20:12.000-06:00", "Sat Jun 11 03:20 PM"),
              ("2011-06-11T15:20:12.000-05:00", "Sat Jun 11 03:20 PM"),
              ("2011-06-11T15:20:12.000-04:00", "Sat Jun 11 03:20 PM"),
              ("2011-06-11T15:20:12.000-03:00", "Sat Jun 11 03:20 PM"),
              
              # Corner cases:
              ("2011-01-01T00:00:00.000-06:00", "Sat Jan  1 12:00 AM"),
              ("2011-01-01T15:40:12.000-06:00", "Sat Jan  1 03:40 PM"),
              ("2011-01-01T23:59:59.000-06:00", "Sat Jan  1 11:59 PM"),
              ("2011-12-31T00:00:00.000-06:00", "Sat Dec 31 12:00 AM"),
              ("2011-12-31T19:02:12.000-06:00", "Sat Dec 31 07:02 PM"),
              ("2011-12-31T23:59:59.000-06:00", "Sat Dec 31 11:59 PM") )

    invalid = ("2011-06-11T15:20:12.00",             # too few digits in microseconds
               "2011-13-11T15:20:12.000-06:00",      # non-existent month
               "2011-04-31T15:20:12.000-06:00",      # non-existent day
               "2011-13-11T15:20:12.000-06:00",      # February 31st
               "2011-06-11C15:20:12.000-06:00",      # wrong TZ separator
               "this is not even remotely a date")   # nonsense

    def testValid(self):
        for input, expected in self.valid:
            self.assertEqual(CreateEventHandler._format_date(input), expected)

    def testInvalid(self):
        for input in self.invalid:
            self.assertRaises(ValueError, CreateEventHandler._format_date, input)


if __name__ == "__main__":
    unittest.main()
