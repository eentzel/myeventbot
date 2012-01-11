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
                        reverse=True)[:30]
        query = ecal.EcalUser.gql("WHERE email_address in :e",
                                  e=[c[1].split("@")[0] for c in counts])
        user_records = query.fetch(30)
        self.response.out.write([(count, email, rec.send_email)
                                 for ((count, email), rec)
                                 in zip(counts, user_records)])


def main():
    application = ecal.EcalWSGIApplication([('/heavy_users', HeavyUsersHandler)])
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
