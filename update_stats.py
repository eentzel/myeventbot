#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
from google.appengine.ext.webapp import util

import ecal


MAX_ACTIONS = 999999


class StatsUpdater(ecal.EcalRequestHandler):
    def get(self):    # TODO: s/b post() because it's definitely not idempotent
        start_time = datetime.datetime.strptime(self.request.get('day'), '%Y-%m-%d')
        end_time = start_time + datetime.timedelta(days=1)
        day = str(start_time.date())

        query = ecal.EcalAction.all()
        query.filter('type =', 'event_created')
        query.filter('time >=', start_time)
        query.filter('time >', end_time)
        actions = query.fetch(MAX_ACTIONS)

        events_created = ecal.EcalStat(key_name='events-created-' + day,
                                       value=len(actions))
        events_created.put()

        unique_users = {}
        for action in actions:
            unique_users[action.user] = True
        num_unique_users = ecal.EcalStat(key_name='unique-users-' + day,
                                         value=len(unique_users))
        num_unique_users.put()


def main():
    application = ecal.EcalWSGIApplication([('/update_stats', StatsUpdater)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()

        
