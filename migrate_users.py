from google.appengine.ext import db
import ecal
import logging


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
        u = ecal.EcalUser.all().filter('schema_version !=', 2).get()
        if u is None:
            logging.info('no users suitable for migration')
            return
        update_one_user(u)


app = ecal.EcalWSGIApplication([('/migrate_one_user', MigrationHandler)])
