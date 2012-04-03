#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

import os
import random
import string

from google.appengine.api import app_identity
from google.appengine.ext import db
import webapp2
from google.appengine.ext.webapp import template

import google_api
import settings


# Constant for datstore queries:
LOTS_OF_RESULTS = 999999


# TODO: @memoize
def get_environment(version=None):
    app_id = app_identity.get_application_id()
    environments = {
        'testing': {
            'base_url': 'http://%s' % (settings.HOST_NAME),
            'secure_base_url': 'http://%s' % (settings.HOST_NAME),
            'rsa_key': None },
        'staging': {
            'base_url':
                'http://%s.%s.appspot.com' % ('staging', app_id),
            'secure_base_url':
                'https://%s.%s.appspot.com' % ('staging', app_id),
            'rsa_key': None },
        'master': {
            'base_url': 'http://www.myeventbot.com',
            'secure_base_url':
                'https://%s.appspot.com' % (app_id),
            'rsa_key': load_rsa_key() } }
    if version is None:
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


class EcalWSGIApplication(webapp2.WSGIApplication):
    def __init__(self, url_mapping):
        debug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
        super(EcalWSGIApplication, self).__init__(url_mapping, debug)


class EcalRequestHandler(webapp2.RequestHandler):
    def canonical(self, path):
        if self.request.environ['SERVER_PORT'] == '443':
            server = get_environment()['secure_base_url']
        else:
            server = get_environment()['base_url']
        return server + path

    def global_template_vals(self):
        return {
            'canonical': self.canonical(self.request.path),
            'auth_link': get_environment()['secure_base_url'] + '/authorize'
            }

    def respond_with_template(self, name, values):
        # TODO: use posixpath.normalize() or some form of whitelisting
        # see http://lucumr.pocoo.org/2010/12/24/common-mistakes-as-web-developer/
        # unit test that 'GET /asdf/../foo.html' and similar return 404
        full_path = os.path.join(os.path.dirname(__file__), 'templates', name)
        all_values = self.global_template_vals()
        all_values.update(values)
        self.response.out.write(template.render(full_path, all_values))
