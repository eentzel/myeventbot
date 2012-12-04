#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

from livecount import counter
import ecal
from google.appengine.ext.webapp.mail_handlers import InboundMailHandler
from google.appengine.ext.deferred import defer
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


def reply_with_logging(message, template_name, values, warning=None):
    if warning is not None:
        logging.warn(warning)
        logging.info("Sender: " + message.sender)
        if hasattr(message, 'subject'):
            logging.info("Subject: " + message.subject)
    outgoing_mail.reply_to(message, template_name, values)


def no_subject(message):
    reply_with_logging(message,
                       'no_subject',
                       {'original_body': message.body},
                       "Couldn't create event because message had no subject")


def no_such_address(message, adr):
    if not hasattr(message, 'subject'):
        message.subject = ''
    reply_with_logging(message,
                       'no_such_address',
                       {'address': adr, 'subject': message.subject},
                       "Couldn't create event for user with address " + adr)


def success(message, event):
    template_vals = {
        'link': event.GetHtmlLink().href,
        'title': event.title.text}
    when = event.FindExtensions(tag='when')
    if len(when) > 0:
        template_vals['when'] = CreateEventHandler._format_date(
            when[0].attributes['startTime'])
    reply_with_logging(message, 'event_created', template_vals)


def token_revoked(message, adr):
    reply_with_logging(message,
                       'token_revoked',
                       {'address': adr, 'subject': message.subject})


def update_stats(user_key, email_adr):
    # counters wanted:
    #     - events created / day over the whole system
    #     - events created / day per user, so we can get the top
    #       N users (maybe for send_emails T/F separately?)
    #     - last action by this user
    # https://developers.google.com/appengine/docs/python/datastore/queries
    day = counter.PeriodType.find_scope(counter.PeriodType.DAY, datetime.now())
    counter.load_and_increment_counter(
        email_adr,
        namespace='top_users_' + day,
        period_types=[counter.PeriodType.DAY])
    counter.load_and_increment_counter(
        'event_created',
        period_types=[counter.PeriodType.DAY, counter.PeriodType.WEEK])


class CreateEventHandler(InboundMailHandler):
    # self.request.path will contain something like:
    # /_ah/mail/f832ofhAau%40myeventbot.appspotmail.com
    def _get_email_address(self):
        decoded_path = urllib.unquote(self.request.path)
        return decoded_path.replace('/_ah/mail/', '')

    def _get_local_part(self):
        return self._get_email_address().split('@')[0]

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
            1) quoted-printable or base64 decoding, performed by
               decode_header()
            2) character set (e.g., utf-8 or iso-8859-1) decoding, performed
               by decode()
            3) conversion into UTF-8, performed by encode()
        """
        try:
            parts = decode_header(header)
            decoded = [value.decode(charset or default)
                       for value, charset in parts]
            return u"".join(decoded).encode('utf-8')
        except UnicodeDecodeError, _:
            logging.exception("Couldn't decode header: " +
                              pickle.dumps(header))

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
        current_user = ecal.EcalUser.get_by_key_name(self._get_local_part())
        if current_user == None:
            return
        if not hasattr(message, 'subject') or message.subject.strip() == '':
            if current_user.send_emails:
                defer(no_subject, message)
            return
        token = current_user.auth_token
        # message.subject = CreateEventHandler.header_to_utf8(message.subject)
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
                    defer(token_revoked, message, self._get_email_address())
            else:
                # Don't know what the error is, let's re-raise it so
                # it gets logged and the message retried
                if 'X-AppEngine-TaskRetryCount' in self.request.headers:
                    logging.warn("Retry count is " + self.request.headers['X-AppEngine-TaskRetryCount'])
                else:
                    logging.warn("No X-AppEngine-TaskRetryCount")
                raise
            return
        else:
            try:
                update_stats(current_user.key(), self._get_local_part())
                if current_user.send_emails:
                    defer(success, message, event)
            except:
                return


app = ecal.EcalWSGIApplication([CreateEventHandler.mapping()])
