#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import os
import atom.url
import gdata.service
import gdata.alt.appengine
import settings
import logging
import uuid
from ecal_users import EmailUser

GCAL_FEED = 'https://www.google.com/calendar/feeds/default/private/full'


class RegistrationHandler(webapp.RequestHandler):
    def get(self):
        client = gdata.service.GDataService()
        gdata.alt.appengine.run_on_appengine(client)
        session_token = None
        auth_token = gdata.auth.extract_auth_sub_token_from_url(self.request.uri)
        if auth_token == None:
            logging.error("Couldn't extract one-time auth token from URL")
            return
        session_token = client.upgrade_to_session_token(auth_token)
        if session_token == None:
            logging.error("Couldn't upgrade to session token")
            return
        myuser = EmailUser()
        myuser.email_address = str(uuid.uuid4())
        myuser.auth_token = str(session_token)
        myuser.put()
        template_values = { 'email_address': myuser.email_address }
        path = os.path.join(os.path.dirname(__file__), 'success.html')
        self.response.out.write(template.render(path, template_values))            

    
class AddEventHandler(webapp.RequestHandler):
    def get(self):
        client = gdata.service.GDataService()
        gdata.alt.appengine.run_on_appengine(client)
        all_users = EmailUser.gql("ORDER BY date_added DESC LIMIT 1")
        for my_user in all_users:
            token_str = my_user.auth_token.split('=')[1]
        token = gdata.auth.AuthSubToken()
        token.set_token_string(token_str)
        client.current_token = token
        xml_data = """<entry xmlns='http://www.w3.org/2005/Atom' xmlns:gCal='http://schemas.google.com/gCal/2005'>
                          <content type="html">Tennis at Hyland Feb 11 3p-3:30</content>
                          <gCal:quickadd value="true"/>
                      </entry>"""
        response = client.Post(xml_data, GCAL_FEED)
        self.response.out.write(response)

class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        template_values = { 'auth_link': self.auth_link() }
        self.response.out.write(template.render(path, template_values))

    def auth_link(self):
        next_url = atom.url.Url('http', settings.HOST_NAME, path='/register')
        client = gdata.service.GDataService()
        gdata.alt.appengine.run_on_appengine(client)
        return client.GenerateAuthSubURL(
            next_url,
            (GCAL_FEED,),
            secure=False, session=True)




def main():
    application = webapp.WSGIApplication([('/', MainHandler),
                                          ('/make_an_event', AddEventHandler),
                                          ('/register', RegistrationHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
