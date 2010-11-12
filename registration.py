#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import os
import google_api
from ecal_users import EmailUser
from ecal_wsgi import EcalWSGIApplication


class RegistrationHandler(webapp.RequestHandler):
    def get(self):
        temp_token = google_api.temp_token_from_url(self.request.uri)
        if temp_token == None:
            self.redirect("/")
            return
        session_token = google_api.permanent_token_from_temp_token(temp_token)
        myuser = EmailUser(auth_token=session_token.get_token_string())
        myuser.put()
        template_values = { 'email_address': myuser.email_address + '@' + os.environ['APPLICATION_ID'] + '.appspotmail.com' }
        path = os.path.join(os.path.dirname(__file__), 'success.html')
        self.response.out.write(template.render(path, template_values))            


def main():
    application = EcalWSGIApplication([('/register', RegistrationHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
