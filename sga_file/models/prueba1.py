# !/usr/bin/python

import os
IN_PATH = "//home/kiko/py10/e10/project-addons/SGA-files/sgafolder/in/"
for root,dirs,files in os.walk(IN_PATH, topdown=False):
    for name in files:
        print name
        print(os.path.join(IN_PATH, name))
