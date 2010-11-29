#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#

import ecal
from email_user import EmailUser
from google.appengine.ext.webapp.util import run_wsgi_app


class MigrationHandler(ecal.EcalRequestHandler):
    def get(self, path):
        all_users = EmailUser.gql("ORDER BY date_added DESC LIMIT 1")
        for my_user in all_users:
            old_user = my_user
        new_user = ecal.EcalUser(email_address=old_user.email_address,
                            auth_token=old_user.auth_token,
                            date_added=old_user.date_added,
                            last_action=old_user.last_action)
        new_user.put()
        old_user.delete()


def main():
    application = ecal.EcalWSGIApplication([(r'/(.*)', MigrationHandler)])
    run_wsgi_app(application)

if __name__ == "__main__":
  main()
