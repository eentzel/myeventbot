from collections import defaultdict
import re
import time

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import logservice
import ecal




class HeavyUsersHandler(ecal.EcalRequestHandler):
    def get(self):
        start_time = time.time() - 24 * 60 * 60
        users = (l.resource.replace('/_ah/mail/', '')
                 for l in logservice.fetch(start_time=start_time)
                 if l.resource.startswith('/_ah/mail/'))
        user_counts = defaultdict(int)
        for u in users:
            user_counts[u] += 1
        self.response.out.write(user_counts)


def main():
    application = ecal.EcalWSGIApplication([('/heavy_users', HeavyUsersHandler)])
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
