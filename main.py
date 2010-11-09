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


class RegistrationHandler(webapp.RequestHandler):
    def get(self):
        temp_token = google_api.temp_token_from_url(self.request.uri)
        session_token = google_api.permanent_token_from_temp_token(temp_token)
        myuser = EmailUser(auth_token=session_token.get_token_string())
        myuser.put()
        template_values = { 'email_address': myuser.email_address }
        path = os.path.join(os.path.dirname(__file__), 'success.html')
        self.response.out.write(template.render(path, template_values))            


class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        template_values = { 'auth_link': google_api.generate_auth_link() }
        self.response.out.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/register', RegistrationHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
