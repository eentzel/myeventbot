from google.appengine.ext import db

class EmailUser(db.Model):
    email_address = db.StringProperty()
    auth_token = db.StringProperty()
    date_added = db.DateTimeProperty()
    last_action = db.DateTimeProperty()
