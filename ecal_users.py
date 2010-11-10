from google.appengine.ext import db
import random
import string

def make_address():
    """
    Returns a random alphanumeric string of 10 digits.  Since
    there are 62 choices per digit, this gives:
    62 ** 10 = 8.39299366 x 10 ** 17

    possible results.  When there are a million accounts active,
    we need:
    10 ** 6 x 10 ** 6 = 10 ** 12

    possible results to have a one-in-a-million chance of a
    collision, so this seems like a safe number.
    """
    chars = string.letters + string.digits
    return ''.join([ random.choice(chars) for i in range(10) ])
        
class EmailUser(db.Model):
    # the email address that the user sends events to:
    email_address = db.StringProperty(default=make_address())
    # the AuthSub token used to authenticate the user to gcal:
    auth_token = db.StringProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
    last_action = db.DateTimeProperty(auto_now_add=True)
