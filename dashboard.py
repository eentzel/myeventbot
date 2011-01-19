#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
from google.appengine.ext.webapp import util

import ecal


DAYS_OF_HISTORY = 9

    
class DashboardHandler(ecal.EcalRequestHandler):
    def unique_users(self):
        users = ecal.EcalUser.all().filter('last_action >=', self.days[-1])
        retval = []
        for day in self.days:
            retval.append(len([u for u in users if u.last_action - day < self.one_day and u.last_action - day >= datetime.timedelta(0)]))
        return retval
    
    def signups(self):
        signups = ecal.EcalUser.all().filter('date_added >=', self.days[-1])
        retval = []
        for day in self.days:
            retval.append(len([u for u in signups if u.date_added - day < self.one_day and u.date_added - day >= datetime.timedelta(0)]))
        return retval

    @staticmethod
    def format_day(day):
        return '<span class="month">%s</span><span class="day">%d</span>' % (day.strftime('%b'), day.day)
        
    def get(self):
        today_start = datetime.datetime.today().replace(hour=0, minute=0,
                                                        second=0, microsecond=0)
        self.one_day = datetime.timedelta(days=1)
        self.days = [today_start - i * self.one_day for i in xrange(0, DAYS_OF_HISTORY)]
        self.respond_with_template('dashboard.html', {
                'signups': self.signups(),
                'days': [self.format_day(d) for d in self.days],
                'uniques': self.unique_users()})


def main():
    application = ecal.EcalWSGIApplication([('/dashboard', DashboardHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
