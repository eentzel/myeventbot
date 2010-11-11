#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
import os


class StaticHandler(webapp.RequestHandler):
    def get(self, path):
        self.response.headers['Cache-Control'] = 'public, max-age=14400'
        full_path = os.path.join(os.path.dirname(__file__), path)
        self.response.out.write(template.render(full_path, None))


def main():
    application = webapp.WSGIApplication([(r'/(.*)', StaticHandler)],
                                         debug = (os.environ['SERVER_NAME'] == 'localhost'))
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
