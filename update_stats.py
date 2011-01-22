#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
from google.appengine.ext.webapp import util

import ecal


class StatsUpdater(ecal.EcalRequestHandler):
    def get(self):
        one_day = datetime.timedelta(days=1)
        if self.request.get('day'):
            start_time = datetime.datetime.strptime(self.request.get('day'), '%Y-%m-%d')
            end_time = start_time + one_day
        else:
            end_time = datetime.datetime.today().replace(hour=0, minute=0,
                                                         second=0, microsecond=0)
            start_time = end_time - one_day
        day = start_time.date()

        query = ecal.EcalAction.all()
        query.filter('type =', 'event_created')
        query.filter('time >=', start_time)
        query.filter('time <', end_time)
        actions = query.fetch(ecal.LOTS_OF_RESULTS)

        events_created = ecal.EcalStat(key_name='events-created-' + str(day),
                                       type='events-created',
                                       day=day,
                                       value=len(actions))
        events_created.put()

        unique_users = {}
        for action in actions:
            unique_users[action.user] = True
        num_unique_users = ecal.EcalStat(key_name='unique-users-' + str(day),
                                         type='unique-users',
                                         day=day,
                                         value=len(unique_users))
        num_unique_users.put()


def main():
    application = ecal.EcalWSGIApplication([('/update_stats', StatsUpdater)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
