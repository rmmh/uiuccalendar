from google.appengine.ext import db

class Schedule(db.Model):
    text = db.TextProperty()
    date = db.DateTimeProperty(auto_now_add=True)
    ip = db.StringProperty()
