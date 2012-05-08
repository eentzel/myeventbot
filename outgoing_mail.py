#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

from google.appengine.api import mail
from google.appengine.ext.webapp import template
from google.appengine.api import memcache
from datetime import datetime
import os


from_address = '"EventBot" <admin@myeventbot.com>'
email_interval = 10


# TODO: the memcache rate-limiting part of this might make a nice decorator

# TODO: swallow over quota exception so tasks don't back up

def send(to, template_name, values, extra_headers=None):
    """Send an email to the specified address using a template.  No
    more than one email per EMAIL_INTERVAL seconds will be sent to any
    given address.
    """
    last_action = memcache.get(to, namespace='last_action')
    if last_action != None:
        return
    path = os.path.join(os.path.dirname(__file__), 'email_templates', template_name)
    message = mail.EmailMessage(sender=from_address, to=to)
    message.subject = template.render(path + '.subject', values)
    message.body = template.render(path + '.body', values)
    if extra_headers is not None:
        message.headers = extra_headers
    message.send()
    memcache.set(to, datetime.now(), time=email_interval, namespace='last_action')

def construct_references(msg):
    """Construct the correct (according to http://cr.yp.to/immhf/thread.html)
    References: header for a reply to MSG"""
    if 'Message-ID' in msg.original:
        if 'References' in msg.original:
            return msg.original['References'] + ' ' + msg.original['Message-ID']
        return msg.original['Message-ID']

def reply_to(message, template_name, values):
    references = construct_references(message)
    if references is not None:
        send(message.sender, template_name, values, extra_headers={'References': references})
    else:
        send(message.sender, template_name, values)
