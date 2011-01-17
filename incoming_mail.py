#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

import ecal
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from gdata.service import RequestError
from email.header import decode_header
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
        recipient = self.message.sender
        if hasattr(self, 'warning'):
            logging.warn(self.warning)
            logging.info("Sender: " + recipient)
            logging.info("Subject: " + self.message.subject)
        try:
            outgoing_mail.send(recipient, self.template_name, self.values())                
        except Exception, err:
            logging.exception("unable to send email to %s using template %s" %
                              (recipient, self.template_name))


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
        str = re.sub(r".000[-+Z].*$", "", str)
        try:
            date = datetime.strptime(str, "%Y-%m-%dT%H:%M:%S")
            retval = date.strftime("%a %b %e %I:%M %p")
        except ValueError:
            date = datetime.strptime(str, "%Y-%m-%d")            
            retval = date.strftime("%a %b %e")
        retval = retval.replace('  ', ' ')
        retval = retval.replace(' 0', ' ')
        return retval

    @staticmethod
    def header_to_unicode(header):
        """It appears that GAE does not decode rfc2047-encoded headers
        for us, so we have to do it manually.  Up to three steps may
        be needed:
            1) quoted-printable or base64 decoding, performed by decode_header()
            2) character set (e.g., utf-8 or iso-8859-1) decoding, performed by decode()
            3) conversion into Unicode, performed by unicode()
        """
        raw = decode_header(header)
        retval = []
        for part in raw:
            value = part[0]
            charset = part[1]
            if charset:
                value = value.decode(charset)
            if not isinstance(value, unicode):
                value = unicode(value)
            retval.append(value)
        return ''.join(retval)

    def receive(self, message):
        logging.info("Receiving Subject: " + message.subject)
        logging.info("Receiving original Subject: " +
                     message.original['Subject'])
        current_user = self._get_user()
        if current_user == None:
            NoSuchAddressHandler(message, self._get_email_address()).send()
            return
        token = current_user.auth_token
        subject = CreateEventHandler.header_to_unicode(message.subject)
        logging.info("Decoded Subject: " + subject)
        # TODO: everything after this point should move into a task queue
        try:
            event = google_api.quickadd_event_using_token(subject, token)
        except RequestError, err:
            if err.args[0]['status'] == 401:
                TokenRevokedHandler(message, self._get_email_address()).send()
            else:
                # TODO: should probably re-raise the exception,
                # otherwise RequestErrors other than 401 will silently
                # fail to create the event
                logging.exception("couldn't create event")
            return
        current_user.last_action = datetime.now()
        current_user.put()
        SuccessHandler(message, event).send()


def main():
    application = ecal.EcalWSGIApplication([CreateEventHandler.mapping()])
    run_wsgi_app(application)

if __name__ == "__main__":
  main()
