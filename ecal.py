#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

import os
import random
import string

import atom.url
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.api.app_identity import get_application_id

import google_api
import settings


# Constant for datstore queries:
LOTS_OF_RESULTS = 999999


def current_environment():
    environments = {
        'testing': {
            'base_url': 'http://%s/' % (settings.HOST_NAME),
            'secure_base_url': 'http://%s/' % (settings.HOST_NAME),
            'rsa_key': None },
        'staging': {
            'base_url':
                'http://%s.%s.appspot.com/' % ('staging', get_application_id()),
            'secure_base_url':
                'http://%s.%s.appspot.com/' % ('staging', get_application_id()),
            'rsa_key': None },
        'master': {
            'base_url': 'http://www.myeventbot.com/',
            'secure_base_url':
                'https://%s.appspot.com/' % (get_application_id()),
            'rsa_key': load_rsa_key() } }
    version = os.environ['CURRENT_VERSION_ID'].split('.')[0]
    return environments[version]

def load_rsa_key():
    f = open(os.path.join(os.path.dirname(__file__), 'myrsakey.pem'))
    rsa_key = f.read()
    f.close()
    return rsa_key


class RandomAddressProperty(db.StringProperty):
    def default_value(self):
        """
        Returns a random alphanumeric (lowercase) string of 9 digits.
        Since there are 32 choices per digit (we exclude 'o', 'l', '0'
        and '1' for readability), this gives:
        32 ** 9 = 3.51843721 x 10 ** 13

        possible results.  When there are a million accounts active,
        we need:
        10 ** 6 x 10 ** 6 = 10 ** 12

        possible results to have a one-in-a-million chance of a
        collision, so this seems like a safe number.
        """
        chars = string.lowercase + string.digits
        chars = chars.translate(string.maketrans('', ''), 'ol01')
        return ''.join([ random.choice(chars) for i in range(9) ])


class EcalUser(db.Model):
    # the email address that the user sends events to:
    email_address = RandomAddressProperty()
    # the AuthSub token used to authenticate the user to gcal:
    auth_token = db.StringProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
    last_action = db.DateTimeProperty()
    google_account = db.UserProperty(auto_current_user_add=True)
    google_account_id = db.StringProperty()
    send_emails = db.BooleanProperty(default=True)


class EcalAction(db.Model):
    type = db.StringProperty()
    time = db.DateTimeProperty(auto_now_add=True)
    user = db.ReferenceProperty(EcalUser)


class EcalStat(db.Model):
    type = db.StringProperty()
    day = db.DateProperty()
    value = db.IntegerProperty()


class EcalWSGIApplication(webapp.WSGIApplication):
    def __init__(self, url_mapping):
        debug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
        super(EcalWSGIApplication, self).__init__(url_mapping, debug)


class EcalRequestHandler(webapp.RequestHandler):
    def canonical(self, path):
        if os.environ['SERVER_PORT'] == '443':
            server = 'https://' + get_application_id() + 'appspot.com'
        else:
            server = 'http://www.myeventbot.com'
        # TODO: canonical URL below sometimes (always?) has an extra
        # '/'.  Need to devise a unit test to catch this, and then
        # fix.
        return server + '/' + path

    def global_template_vals(self):
        return {
            'canonical': self.canonical(self.request.path),
            'auth_link': atom.url.Url('https', get_application_id() + '.appspot.com', path='/authorize')
            }

    def respond_with_template(self, name, values):
        # TODO: use posixpath.normalize() or some form of whitelisting
        # see http://lucumr.pocoo.org/2010/12/24/common-mistakes-as-web-developer/
        # unit test that 'GET /asdf/../foo.html' and similar return 404
        full_path = os.path.join(os.path.dirname(__file__), 'templates', name)
        all_values = self.global_template_vals()
        all_values.update(values)
        self.response.out.write(template.render(full_path, all_values))
