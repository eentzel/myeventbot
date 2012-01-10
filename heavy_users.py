import re
import time

from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.api import logservice
import ecal




class HeavyUsersHandler(ecal.EcalRequestHandler):
    def get(self):
        start_time = time.time() - 24 * 60 * 60
        logs = logservice.fetch(start_time=start_time)
        unique_users = set([l.resource.replace('/_ah/mail/', '')
                            for l in logs
                            if l.resource.startswith('/_ah/mail/')])
        self.response.out.write(unique_users)


def main():
    application = ecal.EcalWSGIApplication([('/heavy_users', HeavyUsersHandler)])
    run_wsgi_app(application)


if __name__ == '__main__':
    main()
