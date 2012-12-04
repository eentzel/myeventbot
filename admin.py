#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
import logging

from google.appengine.api import logservice
from google.appengine.ext import db

from livecount import counter
import ecal
import rest


DAYS_OF_HISTORY = 9


def value_from_list(list, func, default=0):
    matches = filter(func, list)
    if len(matches) == 0:
        return default
    return matches[0].value

def fst(t):
    return t[0]

def iterlen(i):
    return len(list(i))


class HeavyUsersHandler(ecal.EcalRequestHandler):
    def get(self):
        if 'day' in self.request.GET:
            day = self.request.GET['day']
        else:
            day= str(datetime.datetime.now())[0:10]
        q = counter.LivecountCounter.all()
        q.filter('namespace = ', 'top_users_' + day)
        q.order('-count')
        counts = sorted(q.fetch(limit=30), key=lambda x: x.name)

        user_records = ecal.EcalUser.get_by_key_name([c.name for c in counts])
        user_records.sort(key=lambda x: x.email_address)

        template_vals = {
            'users': [
                {
                    'count': c.count,
                    'email': c.name,
                    'send_confirmation': u.send_emails,
                    'toggle_url': '/admin/rest/user/%s/send_emails' % (u.key())
                    }
                for c, u in sorted(zip(counts, user_records),
                                   key=lambda x: x[0].count, reverse=True)]}
        self.respond_with_template('heavy_users.html', template_vals)


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

    # SELECT * FROM LivecountCounter WHERE __key__=Key('LivecountCounter', 'default:day:2012-08-19:event_created')

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


rest.Dispatcher.base_url = '/admin/rest'
rest.Dispatcher.add_models({
        'user': ecal.EcalUser
        })

app = ecal.EcalWSGIApplication([
        ('/admin/rest/.*', rest.Dispatcher),
        ('/admin/dashboard', DashboardHandler),
        ('/admin/heavy_users', HeavyUsersHandler)])
