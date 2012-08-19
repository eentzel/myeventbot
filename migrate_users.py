from google.appengine.api import taskqueue
from google.appengine.ext import db
from google.appengine.runtime import apiproxy_errors
import ecal
import logging


# Use http://blog.notdot.net/2010/05/Exploring-the-new-mapper-API to add schema_version=1 first
from mapreduce import operation as op


def set_schema1(entity):
    if not hasattr(entity, 'schema_version') or entity.schema_version is None:
        entity.schema_version = 1
        yield op.db.Put(entity)
    else:
        logging.info("skipping " + str(entity.key()))
        logging.info("already has schema_version=" + str(entity.schema_version))



@db.transactional(xg=True)
def update_one_user(u):
    """Given an old EcalUser (schema version < 2), replace it with a new
    EcalUser (schema version 2)"""

    if hasattr(u, 'schema_version') and u.schema_version >= 2:
        logging.info(u.email_address + ' not suitable for migration')
        return

    new_user = ecal.EcalUser(email_address=u.email_address,
                             key_name=u.email_address, # this is the good bit
                             auth_token=u.auth_token,
                             date_added=u.date_added,
                             last_action=u.last_action,
                             google_account=u.google_account,
                             google_account_id=u.google_account_id,
                             send_emails=u.send_emails,
                             schema_version=2) # this is the other good bit
    u.delete()
    new_user.put()
    logging.info("migrated user " + new_user.email_address)


class MigrationHandler(ecal.EcalRequestHandler):
    def get(self):
        done = True
        try:
            for u in ecal.EcalUser.all().filter('schema_version !=', 2).run(limit=50):
                update_one_user(u)
                done = False
        except apiproxy_errors.OverQuotaError, message:
            logging.exception(message)
        else:
            if not done:
                taskqueue.add(url='/migrate_fifty_users')
        if done:
            logging.info('Migration complete')


app = ecal.EcalWSGIApplication([('/migrate_fifty_users', MigrationHandler)])
