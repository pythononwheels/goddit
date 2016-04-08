#!/usr/bin/env python
#
# simple tornado server / khz 2016
#
# based on: https://github.com/tornadoweb/tornado/tree/stable/demos/blog
#

import os.path
import re

import tornado.escape
import tornado.httpserver
import tornado.ioloop
import tornado.options
import tornado.web
import config
from tornado.options import define, options
#from handlers import CommentsHandler

define("port", default=8080, help="run on the given port", type=int)

class Application(tornado.web.Application):
    def __init__(self, root_path):
        handlers = [
            #(r"/comments/.*", CommentsHandler),
            (r"/(.*)", tornado.web.StaticFileHandler, {"path": root_path, "default_filename": config.settings["index_filename"]})
        ]
        settings = dict(
            template_path=os.path.join(os.path.dirname(__file__), config.settings["template_path"]),
            static_path=os.path.join(os.path.dirname(__file__),
                os.path.join(config.settings["site_path"], config.settings["static_path"])),
            debug=True,
            autoescape=None
        )
        super(Application, self).__init__(handlers, **settings)

def main(root_path):
    tornado.options.parse_command_line()
    http_server = tornado.httpserver.HTTPServer(Application(root_path))
    http_server.listen(options.port)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    root = os.path.join(os.path.dirname(__file__), config.settings["site_path"])
    print(" ... serving from: " + root)
    #os.chdir(root)
    main(root)
