#
# generate_blog
#
import datetime
from time import strftime

import os, imp
import time
import socket
import shutil
from os.path import isfile, join
import json
import pprint
import argparse
from timeit import default_timer as timer
import tweepy
from pydoc import locate
import hashlib
import json
from operator import itemgetter
import math
from tornado import template
import theme_configs

from config import settings
from tinydb import TinyDB, Query, where


# a pretty printer if you need one ;)
pp = pprint.PrettyPrinter(indent=4)

# some genral definitions
dashes = 80
exclude_files = ["__init__.py", ".DS_Store"]


# configure the template loader
# (http://www.tornadoweb.org/en/stable/template.html#tornado.template.Loader)
if settings["autoescape"]:
    loader = template.Loader("./layouts")
else:
    loader = template.Loader("./layouts", autoescape=None)


def cleandir(path):
    """
        erases the given path tree
    """
    try:
        shutil.rmtree(os.path.join(settings["site_path"],path))
        print(" ... cleaned: " +  os.path.join(settings["site_path"],path) + "directory ...")
    except (FileNotFoundError, PermissionError) as e:
        print(" ... Error" + str(e))


def cleanup():
    '''
        cleans the site dir to be prepared for a new run
        Leaves post and page path untouched to support incremental builds
    '''

    print(dashes*"-")
    print("... Cleaning up: ...")
    print(dashes*"-")
    # remove all files
    cleandir(settings["static_path"])

    path= os.path.abspath(os.path.join(".",settings["site_path"]))
    try:
        os.mkdir(path)
    except Exception as e:
        print("Error creating site_path dir " + str(e))
        
    all =[os.path.join(path,f) for f in os.listdir(path) if os.path.isfile(os.path.join(path, f))]
    #for f in all:
    #    print(" ... removing: " + str(f))
    #    os.remove(os.path.join(path,f))

    if not os.path.exists(settings["site_path"]):
        os.makedirs(settings["site_path"])


def copy_to_site():
    """
        copy the static folder to site_path
    """
    print(dashes*"-")
    print("... Copy to site dir: ... " + settings["site_path"] )
    print(dashes*"-")
    import distutils
    from distutils import dir_util
    distutils.dir_util.copy_tree(settings["static_path"], os.path.join(settings["site_path"], settings["static_path"]))
    print(" ... copied " + settings["static_path"])

def generate_board():
    """
        renders the templates.
        and copies them over to site_path
        all files will be named filename.tmpl = filename.html
        exception: you can specify an index_file in theme_configs. this file will be named index.html
        (0f course you can rename the files manually at will. )
    """
    templates = [f for f in os.listdir(os.path.join(settings["template_path"], settings["theme"]))]
    now = strftime("%a, %d %b %Y %H:%M:%S %z")
    for t in templates:
        out = loader.load(
            os.path.join(settings["theme"],t)).generate(
                now=now, settings=settings)
        fname,fext = os.path.splitext(os.path.split(t)[-1])
        try:
            if settings["index_file"] == t:
                fname = settings["index_filename"]
            else:
                fname = fname + ".html"
        except:
            fname = fname+".html"
        opath = os.path.normpath(os.path.join(settings["site_path"], fname))
        print(" ... writing file: " + opath )
        ofile = open(opath, "wb" )
        ofile.write(out)
        ofile.close()
    return

if __name__ == "__main__":

    start = timer()

    parser = argparse.ArgumentParser(description='goddit. a fully twitter baed message board.')

    parser.add_argument('-a', '--absolute-urls', dest='abs_urls', action='store_true',
        default=False, help='create absolute url links based on the real domain set in settings.json')

    args = parser.parse_args()
    #print("... Arguments:::" + str(args))

    #
    # merge the theme settings with config.settings
    #
    try:
        # aftert this, every attribute in settings will be overwritten by
        # an attribute from theme_configs with the same name.
        # also every complementing attr from theme_configs will be in setting saditionally
        #new_settings = setings.copy()
        settings.update(getattr(theme_configs, settings["theme"]))
    except:
        print(" ... could not load the theme config for : " + settings["theme"])

    print(dashes*"-")
    print("... generating board ...")


    #
    # cleanup site dir
    #
    cleanup()

    copy_to_site()

    generate_board()
    # microseconds or 1/1ß00th of seconds depending on OS.
    # see: https://docs.python.org/3/library/timeit.html
    #
    end = timer()
    print(dashes*"-")
    print("... Built your board in: " + str(end - start) + " seconds")
