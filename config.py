#
# static.py settings
#
import collections
import json

settings = json.load(open("settings.json", "r"), object_pairs_hook=collections.OrderedDict)
