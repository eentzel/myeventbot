#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import datetime
from google.appengine.ext.webapp import util

import ecal


class DashboardHandler(ecal.EcalRequestHandler):
    def get(self):
        one_day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        query = ecal.EcalUser.all().filter('date_added >=', one_day_ago)
        self.respond_with_template('dashboard.html', {'signups': query.count()})


def main():
    application = ecal.EcalWSGIApplication([('/dashboard', DashboardHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
