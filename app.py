import logging
import os
import traceback
from datetime import datetime

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

import convert

from model import Schedule


class UIUCCalendar(webapp.RequestHandler):
    def get(self):
        page = os.path.join(os.path.dirname(__file__), 'index.html.tmpl')
        self.response.out.write(template.render(page, values))

    def post(self):
        schedule = self.request.get('schedule', '')

        if len(schedule) > 20000:
            self.error(413) # error: content too long
            return

        sched = Schedule()
        sched.text = schedule
        sched.ip = self.request.remote_addr

        classes = convert.parse_schedule(schedule)

        if classes == []:
            self.response.out.write("error: unable to find any valid class "
                    "entries. Try re-reading the instructions, and make "
                    "sure that you've copied the table correctly.")
            self.response.set_status(400)
            return

        page = os.path.join(os.path.dirname(__file__), 'template.ics')
        self.response.headers['Content-Type'] = 'application/octet-stream'
        self.response.out.write(template.render(page, {"classes":classes}))
        sched.put()
    
application = webapp.WSGIApplication([('/.*', UIUCCalendar)],debug=True)

def main():
    run_wsgi_app(application)

if __name__ == "__main__":
    main()
