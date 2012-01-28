import os
from xml.sax.saxutils import escape

import atom.url
import gdata.service
import gdata.alt.appengine
from google.appengine.api.app_identity import get_application_id

import ecal


GCAL_FEED = 'https://www.google.com/calendar/feeds/default/private/full'
# TODO: always use secure tokens, need a separate RSA key for dev, staging, prod


def get_client():
    client = gdata.service.GDataService()
    gdata.alt.appengine.run_on_appengine(client, deadline=10)
    return client

def get_client_with_token(token_str):
    client = get_client()
    rsa_key = ecal.get_environment()['rsa_key']
    if rsa_key is None:
        token = gdata.auth.AuthSubToken()
    else:
        token = gdata.auth.SecureAuthSubToken(rsa_key)
    token.set_token_string(token_str)
    client.current_token = token
    return client

def generate_auth_link(app_version=None):
    env = ecal.get_environment(app_version)
    register_url = env['secure_base_url'] + '/register'
    secure = (env['rsa_key'] is not None)
    client = get_client()
    url = client.GenerateAuthSubURL(register_url,
                                    GCAL_FEED,
                                    secure=secure,
                                    session=True,
                                    # lets the URL work with Google
                                    # Apps calendars as well as
                                    # calendar.google.com ones:
                                    domain=None)
    return str(url)

def temp_token_from_url(url):
    return gdata.auth.extract_auth_sub_token_from_url(
        url, rsa_key=ecal.get_environment()['rsa_key'])

def permanent_token_from_temp_token(temp_token):
    session_token = None
    client = get_client()
    session_token = client.upgrade_to_session_token(temp_token)
    return session_token

def quickadd_event_using_token(event, token_str):
    client = get_client_with_token(token_str)
    xml_data = """<?xml version='1.0' encoding='utf-8'?>
                  <entry xmlns='http://www.w3.org/2005/Atom' xmlns:gCal='http://schemas.google.com/gCal/2005'>
                      <content type="html">%s</content>
                      <gCal:quickadd value="true"/>
                  </entry>""" % escape(event)
    # TODO: might be over-escaping - '&' in email subject
    # shows up as '&amp;' in event titles
    return client.Post(xml_data, GCAL_FEED)

def delete_event_using_token(event_url, token_str):
    client = get_client_with_token(token_str)
    return client.Delete(event_url)
