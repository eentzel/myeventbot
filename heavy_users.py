from collections import defaultdict
import itertools
import re
import time

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import logservice
import ecal


def fst(t):
    return t[0]

def iterlen(i):
    return len(list(i))


class HeavyUsersHandler(ecal.EcalRequestHandler):
    def get(self):
        start_time = time.time() - 24 * 60 * 60
        users = sorted((l.resource.replace('/_ah/mail/', ''), 1)
                       for l in logservice.fetch(start_time=start_time)
                       if l.resource.startswith('/_ah/mail/'))
        counts = sorted([(iterlen(group), key) for key, group in
                         itertools.groupby(users, fst)],
                        reverse=True)
        self.response.out.write(counts)


def main():
    application = ecal.EcalWSGIApplication([('/heavy_users', HeavyUsersHandler)])
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
