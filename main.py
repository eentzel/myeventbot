#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import os
import logging
import uuid
import google_api
from ecal_users import EmailUser


class RegistrationHandler(webapp.RequestHandler):
    def get(self):
        temp_token = google_api.temp_token_from_url(self.request.uri)
        if temp_token == None:
            logging.error("Couldn't extract one-time auth token from URL")
            return
        session_token = google_api.permanent_token_from_temp_token(temp_token)
        myuser = EmailUser()
        myuser.email_address = str(uuid.uuid4())
        myuser.auth_token = str(session_token)
        myuser.put()
        template_values = { 'email_address': myuser.email_address }
        path = os.path.join(os.path.dirname(__file__), 'success.html')
        self.response.out.write(template.render(path, template_values))            

    
class AddEventHandler(webapp.RequestHandler):
    def get(self):
        all_users = EmailUser.gql("ORDER BY date_added DESC LIMIT 1")
        for my_user in all_users:
            token_str = my_user.auth_token.split('=')[1]
        response = google_api.quickadd_event_using_token('Tennis at Hyland Feb 11 3p-3:30', token_str)
        self.response.out.write(response)

class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        template_values = { 'auth_link': google_api.generate_auth_link() }
        self.response.out.write(template.render(path, template_values))


def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/make_an_event', AddEventHandler),
                                          ('/register', RegistrationHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
