DESCRIPCIÓN
===========

Este módulo mantiene sincronizada una base de datos secundaria (MongoDB) con una estructura diferente a la de Odoo a la vez que 
gestiona los usuarios y envía los mensajes de actualización a cada uno de ellos mediante Google Cloud Pub/Sub.

REQUISITOS PREVIOS
==================

Instalar la librería pymongo 3.9.0, slugify 0.0.1 y google-cloud (instrucciones con virtualenv):

$ cd sandbox/bin
$ source activate
$ pip install pymongo
$ pip install slugify
$ pip install google-cloud-pubsub
$ pip install --upgrade google-api-python-client google-auth google-auth-httplib2
$ deactivate

Si no conseguimos instalar la librería pymongo con PIP podemos hacerlo manualmente:

$ git clone git://github.com/mongodb/mongo-python-driver.git pymongo
$ cd pymongo/
$ python setup.py install

Esto nos creará un fichero .egg con la librería, podemos copiarla (mejor un link simbólico) a odoo/eggs/ e incluirla en el fichero "start_odoo"

$ ln -s /usr/lib/python2.7/site-packages/pymongo-3.9.0-py2.7-linux-x86_64.egg /opt/odoo/odoo_JIM_10/eggs/pymongo-3.9.0-py2.7-linux-x86_64.egg
