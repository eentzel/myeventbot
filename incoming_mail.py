#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

from ecal_wsgi import EcalWSGIApplication
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from gdata.service import RequestError
import logging
import urllib
from datetime import datetime
from ecal_users import EmailUser
import google_api
import outgoing_mail
import re


class CreateEventHandler(InboundMailHandler):
    # self.request.path will contain something like:
    # /_ah/mail/89c33b71-b5a3-4e0a-bbb3-8283d337cbca%40myeventbot.appspotmail.com
    def _get_email_address(self):
        decoded_path = urllib.unquote(self.request.path)
        return decoded_path.replace('/_ah/mail/', '')

    def _get_user(self):
        local_part = self._get_email_address().split('@')[0]
        query = EmailUser.gql("WHERE email_address = :email", email=local_part)
        try:
            current_user = query.fetch(1)[0]
            return current_user
        except IndexError:
            return None

    @staticmethod
    def _format_date(str):
        """Format a date from GCal into a user-friendly string.

        >>> CreateEventHandler._format_date("2011-02-11T15:00:00.000-07:00")
        'Fri Feb 11 03:00 PM'
        >>> CreateEventHandler._format_date("2011-06-11T15:20:12.000-06:00")
        'Sat Jun 11 03:20 PM'
        """
        # TODO: Remove leading zero from hour
        str = re.sub(r".000-.*$", "", str)
        try:
            date = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
            return date.strftime("%a %b %e %I:%M %p")
        except ValueError:
            date = datetime.strptime(str, "%Y-%m-%d")            
            return date.strftime("%a %b %e")

    def receive(self, message):
        current_user = self._get_user()
        if current_user == None:
            adr = self._get_email_address()
            outgoing_mail.send(message.sender, 'no_such_address',
                               { 'address': adr,
                                 'subject': message.subject })
            logging.warn("Couldn't create event for user with address " + adr)
            return
        token = current_user.auth_token
        try:
            event = google_api.quickadd_event_using_token(message.subject, token)
        except RequestError, err:
            if err.status == 401:
                logging.info("it looks like you've revoked your token")
            else:
                logging.info("couldn't create event")
            return
        current_user.last_action = datetime.now()
        current_user.put()
        start_time = event.FindExtensions(tag='when')[0].attributes['startTime']
        outgoing_mail.send(message.sender, 'event_created',
                           { 'link': event.GetHtmlLink().href,
                             'when': self._format_date(start_time),
                             'title': event.title.text } )


def main():
    application = EcalWSGIApplication([CreateEventHandler.mapping()])
    run_wsgi_app(application)

if __name__ == "__main__":
  main()
