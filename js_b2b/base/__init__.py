# -*- coding: utf-8 -*-

import os

# BBDD de Odoo
os.environ['ODOO_DB'] = 'JIM_1902'
# Google Cloud
os.environ['GOOGLE_CLOUD_PROJECT_ID'] = 'js-b2b-1572002252254'
BASE_PATH = os.path.dirname(os.path.realpath(__file__))
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(BASE_PATH, 'js-b2b-1572002252254-be577478fce9.json')

import base
import subscribe