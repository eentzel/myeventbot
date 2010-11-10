#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from gdata.service import RequestError
import logging
import urllib
from datetime import datetime
from ecal_users import EmailUser
import google_api


class CreateEventHandler(InboundMailHandler):
    # self.request.path will contain something like:
    # /_ah/mail/89c33b71-b5a3-4e0a-bbb3-8283d337cbca%40myeventbot.appspotmail.com
    def __get_email_address(self):
        decoded_path = urllib.unquote(self.request.path)
        return decoded_path.replace('/_ah/mail/', '')

    def __get_user(self):
        local_part = self.__get_email_address().split('@')[0]
        query = EmailUser.gql("WHERE email_address = :email", email=local_part)
        try:
            current_user = query.fetch(1)[0]
            return current_user
        except IndexError:
            return None

    def receive(self, message):
        current_user = self.__get_user()
        token = current_user.auth_token
        if token == None:
            logging.info("can't find user with that email address")
            return
        try:
            response = google_api.quickadd_event_using_token(message.subject, token)
        except RequestError, err:
            if err.status == 401:
                logging.info("it looks like you've revoked your token")
            else:
                logging.info("couldn't create event")
            return
        current_user.last_action = datetime.now()
        current_user.put()
        logging.info('event creation succeeded: ')
        logging.info( response.GetHtmlLink() )


def main():
    application = webapp.WSGIApplication([CreateEventHandler.mapping()], debug=True)
    run_wsgi_app(application)

if __name__ == "__main__":
  main()
