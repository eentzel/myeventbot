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


def send(to, template_name, values):
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
    message.send()
    memcache.set(to, datetime.now(), time=email_interval, namespace='last_action')
