#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import os
import atom.url
import gdata.service
import gdata.alt.appengine
import settings


class MainHandler(webapp.RequestHandler):
    def get(self):
        path = os.path.join(os.path.dirname(__file__), 'index.html')
        template_values = { 'auth_link': self.auth_link() }
        self.response.out.write(template.render(path, template_values))

    def auth_link(self):
        next_url = atom.url.Url('http', settings.HOST_NAME, path='/success')
        client = gdata.service.GDataService()
        gdata.alt.appengine.run_on_appengine(client)
        return client.GenerateAuthSubURL(
            next_url,
            ('https://www.google.com/calendar/feeds/default/private/full',),
            secure=False, session=True)




def main():
    application = webapp.WSGIApplication([('/', MainHandler)],
                                         debug=True)
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
