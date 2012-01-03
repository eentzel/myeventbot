#!/usr/bin/python
# -*- coding: utf-8 -*-

import glob
import os
import unittest
from incoming_mail import CreateEventHandler
from ecal import EcalUser


class MockRequest(object):
    def __init__(self, path):
        self.path = path


class GetUser(unittest.TestCase):
    def setUp(self):
        self.evt_handler = CreateEventHandler()
        self.evt_handler.initialize(MockRequest(''), None)
        test_user = EcalUser(email_address='test_user')
        test_user.put()

    def testValidUser(self):
        self.evt_handler.request.path = '/_ah/mail/test_user%40myeventbot.appspotmail.com'
        result = self.evt_handler._get_user()
        self.assertEqual(result.email_address, 'test_user')
        self.assertTrue(hasattr(result, 'auth_token'))
        self.assertTrue(hasattr(result, 'date_added'))
        self.assertTrue(hasattr(result, 'last_action'))

    def testNonExistentUser(self):
        self.evt_handler.request.path = '/_ah/mail/non_existent_user%40myeventbot.appspotmail.com'
        result = self.evt_handler._get_user()
        self.assertEqual(result, None)


class HeaderToUTF8(unittest.TestCase):
    valid = ( # From the first user to encounter this bug:
              ("=?UTF-8?B?MjAxMTAwNDEgLSBWaW9sYSAtIEV2ZW50Ym90IHRlc3Qgc2VudCB3aXRoIGZpbGVtYWtlciBTTVRQIDEvMTcvMjAxMSB1bnRpbCAxLzIwLzIwMTE=?=",
               "20110041 - Viola - Eventbot test sent with filemaker SMTP 1/17/2011 until 1/20/2011"),

              # From rfc2047:
              ("=?iso-8859-1?q?this=20is=20some=20text?=", "this is some text"),
              ("=?US-ASCII?Q?Keith_Moore?= <moore@cs.utk.edu>", "Keith Moore<moore@cs.utk.edu>"),
              ("=?ISO-8859-1?Q?Keld_J=F8rn_Simonsen?= <keld@dkuug.dk>", 'Keld Jørn Simonsen<keld@dkuug.dk>'),
              ("=?ISO-8859-1?Q?Andr=E9?= Pirard <PIRARD@vm1.ulg.ac.be>", 'AndréPirard <PIRARD@vm1.ulg.ac.be>'),
              ("=?ISO-8859-1?B?SWYgeW91IGNhbiByZWFkIHRoaXMgeW8=?=\n=?ISO-8859-2?B?dSB1bmRlcnN0YW5kIHRoZSBleGFtcGxlLg==?=",
               u'If you can read this you understand the example.'),
              ("=?ISO-8859-1?Q?Olle_J=E4rnefors?= <ojarnef@admin.kth.se>", 'Olle Järnefors<ojarnef@admin.kth.se>'),
              ("=?ISO-8859-1?Q?Patrik_F=E4ltstr=F6m?= <paf@nada.kth.se>", 'Patrik Fältström<paf@nada.kth.se>'),

              # My test cases:
              ("This has encoded =?iso-8859-1?q?stuff?= in the middle", "This has encodedstuffin the middle"),
              ("This has encoded =?iso-8859-1?q?=20stuff=20?= in the middle", "This has encoded stuff in the middle"),
              ("Not encoded at all", "Not encoded at all"),

              # Empty string
              ("", ""),

              # From Python's email.header docs:
              ('=?iso-8859-1?q?p=F6stal?=', "pöstal") )

    def testValid(self):
        for input, expected in self.valid:
            self.assertEqual(CreateEventHandler.header_to_utf8(input), expected)

    # TODO: negative testcases for incorrectly-encoded strings


class StripBcc(unittest.TestCase):
    def testBcc(self):
        input_filenames = glob.iglob(os.path.join(os.path.dirname(__file__), 'bcc/*.in'))
        for file_name in input_filenames:
            input = open(file_name)
            output = open(file_name.replace('.in', '.out'))
            stripped = CreateEventHandler.strip_bcc(input.read())
            self.assertEqual(stripped, output.read())
            input.close()
            output.close()


class FormatDate(unittest.TestCase):
    valid = ( # PM:
              ("2011-02-11T15:00:00.000-07:00", "Fri Feb 11 3:00 PM"),

              # AM:
              ("2011-06-11T10:08:12.000-06:00", "Sat Jun 11 10:08 AM"),
              ("2011-06-11T08:08:12.000-06:00", "Sat Jun 11 8:08 AM"),

              # Timezone should be ignored:
              ("2011-06-11T15:20:12.000-06:00", "Sat Jun 11 3:20 PM"),
              ("2011-06-11T15:20:12.000-05:00", "Sat Jun 11 3:20 PM"),
              ("2011-06-11T15:20:12.000-04:00", "Sat Jun 11 3:20 PM"),
              ("2011-06-11T15:20:12.000-03:00", "Sat Jun 11 3:20 PM"),

              # Timezone with positive offest:
              ("2011-06-11T15:20:12.000+03:00", "Sat Jun 11 3:20 PM"),

              # TODO: add tests for all-day events ("%Y-%m-%d")

              # Zulu timezone
              ("2011-06-11T15:20:12.000Z", "Sat Jun 11 3:20 PM"),

              # Corner cases:
              ("2011-01-01T00:00:00.000-06:00", "Sat Jan 1 12:00 AM"),
              ("2011-01-01T15:40:12.000-06:00", "Sat Jan 1 3:40 PM"),
              ("2011-01-01T23:59:59.000-06:00", "Sat Jan 1 11:59 PM"),
              ("2011-12-31T00:00:00.000-06:00", "Sat Dec 31 12:00 AM"),
              ("2011-12-31T19:02:12.000-06:00", "Sat Dec 31 7:02 PM"),
              ("2011-12-31T23:59:59.000-06:00", "Sat Dec 31 11:59 PM") )

    invalid = ("2011-06-11T15:20:12.00",             # too few digits in microseconds
               "2011-13-11T15:20:12.000-06:00",      # non-existent month
               "2011-04-31T15:20:12.000-06:00",      # non-existent day
               "2011-02-31T15:20:12.000-06:00",      # February 31st
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
