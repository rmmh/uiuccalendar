import os
from xml.sax.saxutils import unescape

from google.appengine.ext import ndb

import webapp2
import jinja2

import convert


JINJA_ENV = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))


class Schedule(ndb.Model):
    text = ndb.TextProperty()
    date = ndb.DateTimeProperty(auto_now_add=True)
    ip = ndb.StringProperty()


class UIUCCalendar(webapp2.RequestHandler):
    def get(self):
        return self.post()

    def post(self):
        schedule = self.request.get('schedule', '')
        schedule = unescape(schedule)

        if len(schedule) > 20000:
            self.error(413)  # error: content too long
            return

        sched = Schedule(text=schedule, ip=self.request.remote_addr)

        classes = convert.parse_schedule(schedule)

        if classes == []:
            self.response.out.write("error: unable to find any valid class "
                    "entries. Try re-reading the instructions, and make "
                    "sure that you've copied the table correctly.")
            self.response.set_status(400)
            return

        template = JINJA_ENV.get_template('template.ics')
        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.out.write(template.render({"classes": classes}))

        sched.put()


app = webapp2.WSGIApplication([('/.*', UIUCCalendar)])
