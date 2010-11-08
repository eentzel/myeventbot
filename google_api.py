import atom.url
import gdata.service
import gdata.alt.appengine
import settings


GCAL_FEED = 'https://www.google.com/calendar/feeds/default/private/full'


def get_client():
    client = gdata.service.GDataService()
    gdata.alt.appengine.run_on_appengine(client)
    return client
    
def generate_auth_link():
    next_url = atom.url.Url('http', settings.HOST_NAME, path='/register')
    client = get_client()
    return client.GenerateAuthSubURL(next_url, GCAL_FEED, secure=False, session=True)

def temp_token_from_url(url):
    token = gdata.auth.extract_auth_sub_token_from_url(url)
    if token == None:
        raise Exception("Couldn't extract one-time auth token from URL")
    return token

def permanent_token_from_temp_token(temp_token):
    session_token = None
    client = get_client()
    session_token = client.upgrade_to_session_token(temp_token)
    return session_token

def quickadd_event_using_token(event, token_str):
    client = get_client()
    token = gdata.auth.AuthSubToken()
    token.set_token_string(token_str)
    client.current_token = token
    xml_data = """<entry xmlns='http://www.w3.org/2005/Atom' xmlns:gCal='http://schemas.google.com/gCal/2005'>
                      <content type="html">%s</content>
                      <gCal:quickadd value="true"/>
                  </entry>""" % (event)
    return client.Post(xml_data, GCAL_FEED)
