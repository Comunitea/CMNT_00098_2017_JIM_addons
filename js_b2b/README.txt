DESCRIPCIÓN
===========

Este módulo mantiene sincronizada una base de datos secundaria (MongoDB) con una estructura diferente a la de Odoo a la vez que gestiona los usuarios y envía los mensajes de actualización a cada uno de ellos mediante Apache Pulsar.

REQUISITOS PREVIOS
==================

Instalar docker

$ sudo apt install docker.io
$ sudo systemctl start docker
$ sudo systemctl enable docker

Instalar la librería pymongo, pulsar-client y PyJWT (instrucciones con virtualenv):

$ cd sandbox/bin
$ source activate
$ pip install pymongo
$ pip install pulsar-client
$ pip install PyJWT
$ deactivate

Si no conseguimos instalar la librería pymongo con PIP podemos hacerlo manualmente:

$ git clone git://github.com/mongodb/mongo-python-driver.git pymongo
$ cd pymongo/
$ python setup.py install

Esto nos creará un fichero .egg con la librería, podemos copiarla (mejor un link simbólico) a odoo/eggs/ e incluirla en el fichero "start_odoo"

$ ln -s /usr/lib/python2.7/site-packages/pymongo-3.9.0-py2.7-linux-x86_64.egg /opt/odoo/odoo_JIM_10/eggs/pymongo-3.9.0-py2.7-linux-x86_64.egg

Por alguna razón la librería pulsar-client también la instala por defecto fuera del virtualenv, para arreglarlo:

$ cp -r /usr/lib/python2.7/site-packages/pulsar/ ../lib/python2.7/site-packages/pulsar/
$ cp -r /usr/lib/python2.7/site-packages/pulsar_client-2.4.0.dist-info/ ../lib/python2.7/site-packages/pulsar_client-2.4.0.dist-info/
$ cp -r /usr/lib/python2.7/site-packages/_pulsar.so ../lib/python2.7/site-packages/_pulsar.so
$ cp -r /usr/lib/python2.7/site-packages/fastavro/ ../lib/python2.7/site-packages/fastavro/
$ cp -r /usr/lib/python2.7/site-packages/fastavro-0.22.4.dist-info/ ../lib/python2.7/site-packages/fastavro-0.22.4.dist-info/
