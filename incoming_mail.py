#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

import ecal
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from gdata.service import RequestError
import logging
import urllib
from datetime import datetime
import google_api
import outgoing_mail
import re


class FeedbackHandler(object):
    """Abstract class to send email feedback to the user that their
    event creation succeeded/failed.

    Swallows all exceptions so that the HTTP request that GAE sends us
    for incoming mail doesn't throw a 500 error -- if it did, GAE
    would keep retrying and creating duplicate events.

    Subclasses must implement a values() method and a template_name
    attribute.  Subclasses can optionally implement a warning
    attribute, which will be logged.
    """
    def send(self):
        if hasattr(self, 'warning'):
            logging.warn(self.warning)        
        try:
            outgoing_mail.send(self.message.sender, self.template_name,
                               self.values())
        except Exception, err:
            # TODO: should use logging.exception -- see:
            # http://code.google.com/appengine/articles/python/recording_exceptions_with_ereporter.html
            logging.error("unable to send email to %s using template %s" %
                         (self.message.sender, self.template_name))
            logging.error(err)


class NoSuchAddressHandler(FeedbackHandler):
    template_name = 'no_such_address'
    def __init__(self, message, adr):
        self.message = message
        self.adr = adr
        self.warning = "Couldn't create event for user with address " + self.adr
        
    def values(self):
        return { 'address': self.adr,
                 'subject': self.message.subject }


class SuccessHandler(FeedbackHandler):
    template_name = 'event_created'
    def __init__(self, message, event):
        self.message = message
        self.event = event

    def values(self):
        start_time = self.event.FindExtensions(tag='when')[0].attributes['startTime']
        return { 'link': self.event.GetHtmlLink().href,
                 'when': CreateEventHandler._format_date(start_time),
                 'title': self.event.title.text }

    
class TokenRevokedHandler(FeedbackHandler):
    template_name = 'token_revoked'
    def __init__(self, message, adr):
        self.message = message
        self.adr = adr
        self.warning = "Token for address " + self.adr + " doesn't appear to be valid anymore"

    def values(self):
        return { 'address': self.adr,
                 'subject': self.message.subject }
        
        
class CreateEventHandler(InboundMailHandler):
    # self.request.path will contain something like:
    # /_ah/mail/f832ofhAau%40myeventbot.appspotmail.com
    def _get_email_address(self):
        decoded_path = urllib.unquote(self.request.path)
        return decoded_path.replace('/_ah/mail/', '')

    def _get_user(self):
        local_part = self._get_email_address().split('@')[0]
        query = ecal.EcalUser.gql("WHERE email_address = :email", email=local_part)
        return query.get()

    @staticmethod
    def _format_date(str):
        """Format a date from GCal into a user-friendly string."""
        str = re.sub(r".000-.*$", "", str)
        try:
            date = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
            retval = date.strftime("%a %b %e %I:%M %p")
        except ValueError:
            date = datetime.strptime(str, "%Y-%m-%d")            
            retval = date.strftime("%a %b %e")
        retval = retval.replace('  ', ' ')
        retval = retval.replace(' 0', ' ')
        return retval

    def receive(self, message):
        current_user = self._get_user()
        if current_user == None:
            NoSuchAddressHandler(message, self._get_email_address()).send()
            return
        token = current_user.auth_token
        # TODO: everything after this point should move into a task queue
        try:
            event = google_api.quickadd_event_using_token(message.subject, token)
        except RequestError, err:
            if err.args[0]['status'] == 401:
                TokenRevokedHandler(message, self._get_email_address()).send()
            else:
                logging.info("couldn't create event")
            return
        current_user.last_action = datetime.now()
        current_user.put()
        SuccessHandler(message, event).send()


def main():
    application = ecal.EcalWSGIApplication([CreateEventHandler.mapping()])
    run_wsgi_app(application)

if __name__ == "__main__":
  main()
