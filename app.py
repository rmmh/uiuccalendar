import os
from xml.sax.saxutils import unescape

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp

import convert

from model import Schedule


class UIUCCalendar(webapp.RequestHandler):
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

        page = os.path.join(os.path.dirname(__file__), 'template.ics')
        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.out.write(template.render(page, {"classes": classes}))

        sched.put()

app = webapp.WSGIApplication([('/.*', UIUCCalendar)])
