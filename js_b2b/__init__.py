# -*- coding: utf-8 -*-

import os

# Establecer variables de entorno para Google
os.environ['GOOGLE_CLOUD_PROJECT_ID'] = 'js-b2b-1572002252254'
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'static', 'js-b2b-admin-1572002252254-e5f6aaf7609c.json')

import models
import base