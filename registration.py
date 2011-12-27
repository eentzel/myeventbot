#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext.webapp import util
from google.appengine.runtime import apiproxy_errors
from google.appengine.api import users
from google.appengine.api.app_identity import get_application_id

import os
import google_api
import ecal


class RegistrationHandler(ecal.EcalRequestHandler):
    def authorization_denied(self):
        self.redirect("/")

    def authorization_succeeded(self):
        session_token = google_api.permanent_token_from_temp_token(self.temp_token)
        myuser = ecal.EcalUser(
            auth_token=session_token.get_token_string(),
            google_account_id=users.get_current_user().user_id())
        try:
            myuser.put()
        except apiproxy_errors.CapabilityDisabledError:
            template_values = {
                'title': 'Unable to create account',
                'error_text': "We couldn't create your account right now because the database is in read-only mode for maintenance.  Please try again in a few minutes."
                }
            self.respond_with_template('error.html', template_values)
            return
        template_values = { 'email_address': myuser.email_address + '@' + get_application_id() + '.appspotmail.com' }
        self.respond_with_template('success.html', template_values)

    def get(self):
        if self.request.path == '/authorize':
            # TODO: if user is already registered, tell them so
            self.redirect(google_api.generate_auth_link())
        else:
            self.temp_token = google_api.temp_token_from_url(self.request.uri)
            if self.temp_token != None:
                self.authorization_succeeded()
            else:
                self.authorization_denied()


def main():
    application = ecal.EcalWSGIApplication([('/.*', RegistrationHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
