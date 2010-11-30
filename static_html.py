#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
from google.appengine.ext.webapp import util
import ecal


class StaticHandler(ecal.EcalRequestHandler):
    def get(self, path):
        self.response.headers['Cache-Control'] = 'public, max-age=14400'
        if path == "":
            path = "index.html"
        self.respond_with_template(path, {})


def main():
    application = ecal.EcalWSGIApplication([(r'/(.*)', StaticHandler)])
    util.run_wsgi_app(application)


if __name__ == '__main__':
    main()
