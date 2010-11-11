#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import os
import google_api
from ecal_wsgi import EcalWSGIApplication


class StaticHandler(webapp.RequestHandler):
    def get(self, path):
        global_template_vals = None
        self.response.headers['Cache-Control'] = 'public, max-age=14400'
        if path == "":
            path = "index.html"
            global_template_vals = { 'auth_link': google_api.generate_auth_link() }
        full_path = os.path.join(os.path.dirname(__file__), path)
        self.response.out.write(template.render(full_path, global_template_vals))


def main():
    application = EcalWSGIApplication([(r'/(.*)', StaticHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
