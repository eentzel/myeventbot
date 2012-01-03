#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
from google.appengine.ext.webapp import util

import ecal


class StatsUpdater(ecal.EcalRequestHandler):
    def get(self):
        self.init_timeperiod()
        self.update_events_created()
        self.update_unique_users()
        self.update_signups()

    def init_timeperiod(self):
        one_day = datetime.timedelta(days=1)
        if self.request.get('day'):
            self.start_time = datetime.datetime.strptime(self.request.get('day'), '%Y-%m-%d')
            self.end_time = self.start_time + one_day
        else:
            self.end_time = datetime.datetime.today().replace(hour=0, minute=0,
                                                         second=0, microsecond=0)
            self.start_time = self.end_time - one_day
        self.day = self.start_time.date()

    def actions(self):
        if not hasattr(self, 'actions_cache'):
            query = ecal.EcalAction.all()
            query.filter('type =', 'event_created')
            query.filter('time >=', self.start_time)
            query.filter('time <', self.end_time)
            self.actions_cache = query.fetch(ecal.LOTS_OF_RESULTS)
        return self.actions_cache

    def update_events_created(self):
        events_created = ecal.EcalStat(key_name='events-created-' + str(self.day),
                                       type='events-created',
                                       day=self.day,
                                       value=len(self.actions()))
        events_created.put()

    def update_unique_users(self):
        unique_users = {}
        for action in self.actions():
            key = str(action.user.key())
            unique_users[key] = True
        num_unique_users = ecal.EcalStat(key_name='unique-users-' + str(self.day),
                                         type='unique-users',
                                         day=self.day,
                                         value=len(unique_users))
        num_unique_users.put()

    def update_last_action(self):
        pass

    def update_signups(self):
        query = ecal.EcalUser.all()
        query.filter('date_added >=', self.start_time)
        query.filter('date_added <', self.end_time)
        active_users = [u for u in query.fetch(ecal.LOTS_OF_RESULTS)
                        if u.ecalaction_set.count(limit=1) > 0]
        signups = ecal.EcalStat(key_name='signups-' + str(self.day),
                                type='signups',
                                day = self.day,
                                value = len(active_users))
        signups.put()


def main():
    application = ecal.EcalWSGIApplication([('/update_stats', StatsUpdater)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
