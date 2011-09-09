import logging
import os
import traceback
from datetime import datetime

from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import db

from model import Schedule


def hour_from_ampm(hour, ispm):
    # why can't python's strptime just implement %p properly?
    # working with dates: completely terrible in every language
    if hour == 12:
        if not ispm:
            hour = 0
    elif ispm:
        return hour + 12
    return hour


def date_time_to_timestamp(date, clock):
    t = datetime.strptime(date.strip(), "%b %d, %Y")
    c = datetime.strptime(clock.strip(), "%H:%M %p")

    t = t.replace(hour=hour_from_ampm(c.hour, 'pm' in clock), minute=c.minute)

    return datetime.strftime(t, "%Y%m%dT%H%M%S")

def parse_class(line):
    split = line.split('\t')
    if len(split) != 12:
        return

    (crn, course, title, campus, credits, level, 
            start, end, days, time, location, instructor) = split

    if time in ('TBA', 'Time') or not time.strip():
        return

    time_begin, time_end = time.split('-')
    time_begin = date_time_to_timestamp(start, time_begin)
    time_end = date_time_to_timestamp(start, time_end)
    class_end = date_time_to_timestamp(end, "11:59 pm")

    for pair in ('M MO', 'T TU', 'W WE', 'R TH',
            'F FR'):
        short, long = pair.split()
        days = days.replace(short, long + ',')

    days = days.rstrip(',')

    course, section = course.rsplit(' ', 1)

    return dict(crn=crn, course=course, section=section, title=title,
        campus=campus, credits=credits, level=level, 
        start=start, end=end, days=days, time=time,
        time_begin=time_begin, time_end=time_end, class_end=class_end,
        location=location, instructor=instructor)


def parse_schedule(text):
    has_debugged = False

    classes = []
    
    for line in text.splitlines():
        try:
            cls = parse_class(line)
            if cls is not None:
                classes.append(cls)
        except Exception:
            if not has_debugged:
                logging.debug(text)
                has_debugged = True
            logging.warning(traceback.format_exc())

    return classes


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

        classes = parse_schedule(schedule)

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
