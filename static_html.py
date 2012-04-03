#!/usr/bin/env python
#
# Copyright 2010 Eric Entzel <eric@ubermac.net>
#
import ecal


class StaticHandler(ecal.EcalRequestHandler):
    def head(self, path):
        self.get(path)

    def get(self, path):
        self.response.headers['Cache-Control'] = 'public, max-age=14400'
        if path == "":
            path = "index.html"
        self.respond_with_template(path, {})


app = ecal.EcalWSGIApplication([(r'/(.*)', StaticHandler)])
