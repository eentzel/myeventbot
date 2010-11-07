from google.appengine.ext import db

class EmailUser(db.Model):
    # the email address that the user sends events to:
    email_address = db.StringProperty()
    # the AuthSub token used to authenticate the user to gcal:
    auth_token = db.StringProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
