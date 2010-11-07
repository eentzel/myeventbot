from google.appengine.ext import db
import uuid

class EmailUser(db.Model):
    # the email address that the user sends events to:
    email_address = db.StringProperty(default=str(uuid.uuid4()))
    # the AuthSub token used to authenticate the user to gcal:
    auth_token = db.StringProperty()
    date_added = db.DateTimeProperty(auto_now_add=True)
