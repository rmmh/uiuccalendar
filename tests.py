# execute using nosegae:
# nosetests --with-gae --gae-lib-root=$HOME/google_appengine tests

import unittest

import webtest

import app


class HandlerTest(unittest.TestCase):
    def setUp(self):
        self.testapp = webtest.TestApp(app.app)
        self.testbed.activate()
        self.testbed.init_memcache_stub()
        self.testbed.init_datastore_v3_stub()

    def make_fake_schedule(self,
                           start='Jan 1, 2014',
                           end='Jun 1, 2014',
                           days='M',
                           time='8:00 am - 9:30 am'):
        return ('123\tCS123 A1\tNAME\tUC\t8\t1U\t{start}'
                '\t{end}\t{days}\t{time}\tLOC\tTEACHER').format(
            start=start,
            end=end,
            days=days,
            time=time)

    def get_calendar_resp(self, schedule):
        return self.testapp.post('/uiuc_calendar.ics', {'schedule': schedule},
                                 expect_errors=True)

    def get_calendar(self, **kwargs):
        resp = self.get_calendar_resp(self.make_fake_schedule(**kwargs))
        self.assertEqual(resp.status_int, 200)
        return resp.body

    def test_empty(self):
        resp = self.testapp.post('/uiuc_calendar.ics', expect_errors=True)
        self.assertEqual(resp.status_int, 400)

    def test_blank(self):
        resp = self.get_calendar_resp('')
        self.assertEqual(resp.status_int, 400)

    def test_normal(self):
        schedule = '\n'.join(
[
    '43357\tCS 412 P3\tData Mining\tUrbana-Champaign\t3.000\t1U\tAug 22, 2011'
    '\tDec 07, 2011\tWF\t3:30 pm - 4:45 pm\tSiebel Center 1404\tHan',
    '30128\tCS 421 D3\tCompilers\tUrbana-Champaign\t3.000\t1U\tAug 22, 2011'
    '\tDec 07, 2011\tTR\t2:00 pm - 3:15 pm\tSiebel Center 1404\tGunter',
    '45328\tCS 242 AB1\tMixtape\tUrbana-Champaign\t0.000\t1U\tAug 22, 2011'
    '\tDec 07, 2011\tTBA\tSiebel Center for Comp Sci ARR\tWoodley'
])
        resp = self.get_calendar_resp(schedule)
        self.assertEqual(resp.status_int, 200)
        self.assertIn('Data Mining', resp.body)
        self.assertIn('Compilers', resp.body)
        self.assertNotIn('Mixtape', resp.body)  # TBA class -- skipped

    def test_time_am(self):
        ics = self.get_calendar(time='8:00 am - 9:50 am')
        self.assertRegexpMatches(ics, r'DTSTART.*T080000')
        self.assertRegexpMatches(ics, r'DTEND.*T095000')

    def test_time_pm(self):
        ics = self.get_calendar(time='3:00 pm - 4:50 pm')
        self.assertRegexpMatches(ics, r'DTSTART.*T150000')
        self.assertRegexpMatches(ics, r'DTEND.*T165000')

    def test_byday(self):
        ics = self.get_calendar(days='MTWRF')
        self.assertIn(';BYDAY=MO,TU,WE,TH,FR\n', ics)

    def test_repeat_span(self):
        ics = self.get_calendar(start='Jan 10, 2014', end='May 5, 2014')
        self.assertRegexpMatches(ics, r'DTSTART.*:20140110T')
        self.assertRegexpMatches(ics, r'RRULE:FREQ=WEEKLY.*UNTIL=20140505T')

    def test_datastore(self):
        ics = self.get_calendar()
        entries = list(app.Schedule.query())
        self.assertEqual(len(entries), 1)
        self.assertIn('CS123', entries[0].text)
