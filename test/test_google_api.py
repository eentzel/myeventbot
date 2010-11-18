#!/usr/bin/python

import google_api
import unittest
import re

class TempTokenFromUrl(unittest.TestCase):
    def testToken(self):
        url = 'https://myeventbot.appspot.com/register?auth_sub_scopes=https://www.google.com/calendar/feeds/default/private/full&token=1/RuM6SMYS9qDY3oUW-rO9EJlNXOvagzEKo6u0lRld758'
        result =  google_api.temp_token_from_url(url)
        self.assertTrue(hasattr(result, rsa_key))
        self.assertEqual(result.get_token_string(), '1/RuM6SMYS9qDY3oUW-rO9EJlNXOvagzEKo6u0lRld758')

class AddEvent(unittest.TestCase):
    f = open(os.path.join(os.path.dirname(__file__), 'test_token.txt'))
    test_token = f.read()
    f.close()

    def setUp(self):
        self.event = google_api.quickadd_event_using_token('Lunch with Bob Friday at 12', AddEvent.test_token)

    def testValidEvent(self):
        # test basic properties
        self.assertTrue(self.event.GetHtmlLink().href.startswith('https://www.google.com/calendar/event?eid='))
        self.assertEqual(self.event.title.text, 'Lunch with Bob')

        # time should look like: "2011-06-11T15:20:12.000-06:00"
        start_time = self.event.FindExtensions(tag='when')[0].attributes['startTime']
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}-\d{2}:\d{2}", start_time))
        end_time = self.event.FindExtensions(tag='when')[0].attributes['endTime']
        self.assertTrue(re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}.\d{3}-\d{2}:\d{2}", end_time))

    def tearDown(self):
        google_api.delete_event_using_token(self.event.GetEditLink().href, AddEvent.test_token)

        
if __name__ == "__main__":
    unittest.main()
