import atom.url
import gdata.service
import gdata.alt.appengine
import os
from xml.sax.saxutils import escape


GCAL_FEED = 'https://www.google.com/calendar/feeds/default/private/full'
rsa_key = None
debug = os.environ['SERVER_SOFTWARE'].startswith('Dev')
if not debug:
    f = open(os.path.join(os.path.dirname(__file__), 'myrsakey.pem'))
    rsa_key = f.read()
    f.close()


def get_client():
    client = gdata.service.GDataService()
    gdata.alt.appengine.run_on_appengine(client, deadline=10)
    return client

def get_client_with_token(token_str):
    client = get_client()
    if debug:
        token = gdata.auth.AuthSubToken()
    else:
        token = gdata.auth.SecureAuthSubToken(rsa_key)
    token.set_token_string(token_str)
    client.current_token = token
    return client

def generate_auth_link():
    next_url = atom.url.Url('https', os.environ['APPLICATION_ID'] + '.appspot.com', path='/register')
    client = get_client()
    url = client.GenerateAuthSubURL(next_url,
                                    GCAL_FEED,
                                    secure=(not debug),
                                    session=True,
                                    domain=None)
    return str(url)

def temp_token_from_url(url):
    return gdata.auth.extract_auth_sub_token_from_url(url, rsa_key=rsa_key)

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
    return client.Post(xml_data, GCAL_FEED)

def delete_event_using_token(event_url, token_str):
    client = get_client_with_token(token_str)
    return client.Delete(event_url)
