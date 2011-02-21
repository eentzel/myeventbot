#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
from google.appengine.ext.webapp import util

import ecal


DAYS_OF_HISTORY = 9


def value_from_list(list, func, default=0):
    matches = filter(func, list)
    if len(matches) == 0:
        return default
    return matches[0].value


class DashboardHandler(ecal.EcalRequestHandler):
    def all_users(self):
        if not hasattr(self, 'all_users_cache'):
            query = ecal.EcalUser.all().filter('last_action !=', None)
            self.all_users_cache = query.fetch(ecal.LOTS_OF_RESULTS)
        return self.all_users_cache

    def active_users(self):
        return [u for u in self.all_users() if u.last_action > datetime.datetime.now() - datetime.timedelta(days=DAYS_OF_HISTORY)]

    def ecal_stat(self, name):
        query = ecal.EcalStat.all()
        query.filter('day >=', self.days[-1])
        query.filter('day <=', self.days[0])
        query.filter('type =', name)
        query.order('-day')
        stats = query.fetch(ecal.LOTS_OF_RESULTS)
        return [value_from_list(stats, lambda s: s.day == d.date()) for d in self.days]

    @staticmethod
    def format_day(day):
        return '<span class="month">%s</span><span class="day">%d</span>' % (day.strftime('%b'), day.day)
        
    def get(self):
        today_start = datetime.datetime.today().replace(hour=0, minute=0,
                                                        second=0, microsecond=0)
        self.one_day = datetime.timedelta(days=1)
        self.days = [today_start - i * self.one_day for i in xrange(0, DAYS_OF_HISTORY)]
        self.respond_with_template('dashboard.html', {
                'signups': self.ecal_stat('signups'),
                'all_users': len(self.all_users()),
                'active_users': len(self.active_users()),
                'events_created': self.ecal_stat('events-created'),
                'days': [self.format_day(d) for d in self.days],
                'uniques': self.ecal_stat('unique-users')})


def main():
    application = ecal.EcalWSGIApplication([('/dashboard', DashboardHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
