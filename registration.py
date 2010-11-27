#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext.webapp import util
from google.appengine.runtime import apiproxy_errors
import os
import google_api
import ecal


class RegistrationHandler(ecal.EcalRequestHandler):
    def datastore_down_error(self):
        template_values = {
            'title': 'Unable to create account',
            'error_text': "We couldn't create your account right now because the database is in read-only mode for maintenance.  Please try back in a few minutes."
        }
        self.respond_with_template('error.html', template_values)

    def get(self):
        temp_token = google_api.temp_token_from_url(self.request.uri)
        if temp_token == None:
            self.redirect("/")
            return
        session_token = google_api.permanent_token_from_temp_token(temp_token)
        myuser = ecal.EcalUser(auth_token=session_token.get_token_string())
        try:
            myuser.put()
        except apiproxy_errors.CapabilityDisabledError:
            self.datastore_down_error()
            return
        template_values = { 'email_address': myuser.email_address + '@' + os.environ['APPLICATION_ID'] + '.appspotmail.com' }
        self.respond_with_template('success.html', template_values)


def main():
    application = ecal.EcalWSGIApplication([('/register', RegistrationHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
