#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

from google.appengine.api import mail
from google.appengine.ext.webapp import template
import os


from_address = 'EventBot <admin@' + os.environ['APPLICATION_ID'] + '.appspotmail.com>'


def send(to, template_name, values):
    path = os.path.join(os.path.dirname(__file__), 'email_templates', template_name)
    message = mail.EmailMessage(sender=from_address, to=to)
    message.subject = template.render(path + '.subject', values)
    message.body = template.render(path + '.body', values)
    message.send()
