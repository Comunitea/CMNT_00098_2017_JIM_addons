# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html




import os
import re
import sys
import xmlrpclib
import socket
import traceback
import base64
import time


#ODOO CONFIGURACION
ODOO_SERVER = "localhost"
ODOO_DBNAME = 'JIM'
ODOO_USER_NAME = 'admin' #''sga_user'
ODOO_USER_PASSWORD = 'admin' #'sga_user_password'
ODOO_PORT = 8069

#El sistema puede funcionar con ficheros, sin embargo,
#creo que tiene mas rendimiento esto que andar recuperando y buscando paths y options
#TODO REVISAR CUAL ES MAS EFICIENTE
#import settings_sga_file
#IN_FOLDER = settings_sga_file.IN_FOLDER

IN_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/in'
OUT_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/out'
ERROR_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/error'
DELETE_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/delete'
ARCHIVE_FOLDER = '//home/kiko/py10/e10/project-addons/sga_file/sgafolder/archive'
ZIP_FOLDER = ''
DELETE_FILE = False
ERRORS = 3


#Configuraciones

#Indica si proceso fichero completo o solo cabeceras (el resto manualmente ...)
PROCESS = True



class ConnectOdoo:
    """

    """

    def __init__(self):
        """
        Inicializar las opciones por defecto y conectar con odoo
        """


    #-------------------------------------------------------------------------
    #--- WRAPPER XMLRPC OPENERP ----------------------------------------------
    #-------------------------------------------------------------------------


        self.url_template = "http://%s:%s/xmlrpc/%s"
        self.server = ODOO_SERVER#"localhost"
        self.port = ODOO_PORT # 8069
        self.dbname = ODOO_DBNAME #dbname
        self.user_name = ODOO_USER_NAME #'admin'
        self.user_passwd = ODOO_USER_PASSWORD #'admin'
        self.user_id = 0

        #
        # Conectamos con Odoo
        #
        login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
        self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
        self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

        #
        # Fichero Log de Excepciones
        #

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del método create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'create', data, context)

            if isinstance(res, list):
                res = res[0]

            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))

    def search(self, model, query, context={}):
        """
        Wrapper del método search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                model, 'search', query, context)
            return ids
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))

    def read(self, model, ids, fields, context={}):
        """
        Wrapper del método read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'read', ids, fields, context)
            return data
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))

    def write(self, model, ids, field_values, context={}):
        """
        Wrapper del método write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))

    def unlink(self, model, ids, context={}):
        """
        Wrapper del método unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del método default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, ids, context={}):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, method, ids, context)
            return res
        except socket.error, err:
            raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))






    def process_hot_folders(self):
        res = self.execute('product.category', 'sga_file_generate', [], context = False)
        print res
        return res
        res_file = False
        print "-----------------------------------------------------\n" \
              "\n\n\nBuscando ficheros en carpeta \n          %s\n"%IN_FOLDER
        for path, dir, files in os.walk(IN_FOLDER, topdown=False):
            if dir:
                print "         Subcarpeta %s"%dir

            for name in files:
                print "         Encontrado >>> %s" % name
                #mira si hay asociado un sga.file, si no lo crea; devuelve el id y si es nuevo
                res = self.execute('sga.file', 'check_sga_name_xmlrpc',[], {'xmlrpc_filename': name, 'xmlrpc_path': path})
                sga_file = res['sga_file']
                new = res['new']



                if new:
                    print "         Se ha creado sga.file con id: %s"%res['sga_file']
                    res_file = self.execute('sga.file', 'sga_process_file_xmlrpc',[res['sga_file']], {'xmlrpc_header_only': PROCESS})

                elif PROCESS:

                    res_file = self.execute('sga.file', 'sga_process_file_xmlrpc',[res['sga_file']])
                    print "         Se ha procesado el fichero (sga.file [%s])" % res['sga_file']

                print "\n"
        print "-----------------------------------------------------\n"

if __name__ == "__main__":

    ENGINE = ConnectOdoo()

    ENGINE.process_hot_folders()
