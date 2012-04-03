#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

import ecal
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.api import mail
from google.appengine.runtime import apiproxy_errors
from gdata.service import RequestError
from email.header import decode_header
import logging
import urllib
from datetime import datetime
import google_api
import outgoing_mail
import re
import string
import pickle


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
            if hasattr(self.message, 'subject'):
                logging.info("Subject: " + self.message.subject)
        try:
            outgoing_mail.reply_to(self.message, self.template_name, self.values())
        except Exception:
            logging.exception("unable to send email to %s using template %s" %
                              (recipient, self.template_name))


class NoSubjectHandler(FeedbackHandler):
    template_name = 'no_subject'
    warning = "Couldn't create event because message had no subject"
    def __init__(self, message):
        self.message = message
    def values(self):
        return { 'original_body': self.message.body }


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
        retval = { 'link': self.event.GetHtmlLink().href,
                   'title': self.event.title.text }
        when = self.event.FindExtensions(tag='when')
        if len(when) > 0:
            retval['when'] = when[0].attributes['startTime']
        return retval


class TokenRevokedHandler(FeedbackHandler):
    template_name = 'token_revoked'
    def __init__(self, message, adr):
        self.message = message
        self.adr = adr

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
    def header_to_utf8(header, default='utf-8'):
        """It appears that GAE does not decode rfc2047-encoded headers
        for us, so we have to do it manually.  Up to three steps may
        be needed:
            1) quoted-printable or base64 decoding, performed by decode_header()
            2) character set (e.g., utf-8 or iso-8859-1) decoding, performed by decode()
            3) conversion into UTF-8, performed by encode()
        """
        try:
            parts = decode_header(header)
            decoded = [value.decode(charset or default) for value, charset in parts]
            return u"".join(decoded).encode('utf-8')
        except UnicodeDecodeError, _:
            logging.exception("Couldn't decode header: " + pickle.dumps(header))

    @staticmethod
    def strip_bcc(body):
        lines = string.split(body, '\n')
        return '\n'.join([l for l in lines if l[:4] != 'Bcc:'])

    def post(self):
        # Overridden to strip the 'Bcc' header before creating an
        # InboundEmailMessage, since we never need it and
        # InboundEmailMessage barfs on an empty 'Bcc'
        new_body = CreateEventHandler.strip_bcc(self.request.body)
        self.receive(mail.InboundEmailMessage(new_body))

    def receive(self, message):
        current_user = self._get_user()
        if current_user == None:
            NoSuchAddressHandler(message, self._get_email_address()).send()
            return
        if not hasattr(message, 'subject') and current_user.send_emails:
            NoSubjectHandler(message).send()
            return
        token = current_user.auth_token
        message.subject = CreateEventHandler.header_to_utf8(message.subject)
        logging.info("Decoded Subject: " + message.subject)
        # TODO: everything after this point should move into a task queue
        try:
            event = google_api.quickadd_event_using_token(message.subject, token)
        except RequestError, err:
            if err.args[0]['status'] == 401:
                # TODO: we're hitting this when we shouldn't, with a
                # HTTP 401 response "Unknown authorization header".
                # Can we log the headers of the POST we sent, to see
                # if there's anything obviously wrong with them?
                logging.exception("Token doesn't appear to be valid anymore")
                if current_user.send_emails:
                    TokenRevokedHandler(message, self._get_email_address()).send()
            else:
                # Don't know what the error is, let's re-raise it so
                # it gets logged and the message retried
                raise
            return
        try:
            action = ecal.EcalAction(type="event_created", user=current_user)
            action.put()
        except apiproxy_errors.CapabilityDisabledError:
            # The event's already been created, if we can't record the
            # EcalAction, so be it
            pass
        if current_user.send_emails:
            SuccessHandler(message, event).send()


app = ecal.EcalWSGIApplication([CreateEventHandler.mapping()])
