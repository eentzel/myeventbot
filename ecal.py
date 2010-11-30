#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

from google.appengine.ext import db
import random
import string
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from xml.sax.saxutils import escape
import google_api
import os


class RandomAddressProperty(db.StringProperty):
    def default_value(self):
        """
        Returns a random alphanumeric string of 8 digits.  Since there
        are 57 choices per digit (we exclude '0', 'O', 'l', 'I' and '1'
        for readability), this gives:
        57 ** 8 = 1.11429157 x 10 ** 14

        possible results.  When there are a million accounts active,
        we need:
        10 ** 6 x 10 ** 6 = 10 ** 12

        possible results to have a one-in-a-million chance of a
        collision, so this seems like a safe number.
        """
        chars = string.letters + string.digits
        chars = chars.translate(string.maketrans('', ''), '0OlI1')
        return ''.join([ random.choice(chars) for i in range(8) ])


class EcalUser(db.Model):
    # the email address that the user sends events to:
    email_address = RandomAddressProperty()
    # the AuthSub token used to authenticate the user to gcal:
    auth_token = db.StringProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
    last_action = db.DateTimeProperty()        


class EcalWSGIApplication(webapp.WSGIApplication):
    def __init__(self, url_mapping):
        debug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
        super(EcalWSGIApplication, self).__init__(url_mapping, debug)


class EcalRequestHandler(webapp.RequestHandler):
    def canonical(self, path):
        if os.environ['SERVER_PORT'] == '443':
            server = 'https://' + os.environ['APPLICATION_ID'] + 'appspot.com'
        else:
            server = 'http://www.myeventbot.com'
        return server + '/' + path

    def global_template_vals(self):
        return {
            'canonical': self.canonical(self.request.path),
            'auth_link': escape(google_api.generate_auth_link())
            }
    
    def respond_with_template(self, name, values):
        full_path = os.path.join(os.path.dirname(__file__), 'templates', name)
        all_values = self.global_template_vals()
        all_values.update(values)
        self.response.out.write(template.render(full_path, all_values))
