# -*- coding: utf-8 -*-
from odoo import api, models, _
from odoo.exceptions import UserError
from google.cloud import pubsub_v1
from .helper import MsgTypes, OutputHelper
from unidecode import unidecode
import pymongo
import json
import os

# Constants definition
MONGODB_DBN = 'js_exchange'
MONGODB_URL = 'mongodb://192.168.1.207:27017/'
# Configure the batch to publish as soon as there is one kilobyte of data or 30 seconds has passed
batch_settings = pubsub_v1.types.BatchSettings(max_bytes=1024, max_latency=30)
# Create the Pub/Sub publisher object
publisher = pubsub_v1.PublisherClient(batch_settings)
# Init MongoDB
conn = pymongo.MongoClient(MONGODB_URL)
db = conn[MONGODB_DBN]

# Module base class
class BaseB2B(models.AbstractModel):
    _inherit = 'base'

    obj_id = None # Item id
    obj_data = None # Item data dict
    collection = None # Data item name

    def __update_on_mongodb(self, mode):
        # Object primary key
        obj_key = { '_jim_id': self.obj_id }
        # Set id into data for create mode
        create_data = self.obj_data.copy()
        create_data.update(obj_key)
        # Define posible actions
        try:
            if mode == 'create':
                db[self.collection].insert_one(create_data)
            if mode == 'update':
                db[self.collection].update_one(obj_key, { "$set": self.obj_data })
            if mode == 'delete':
                db[self.collection].delete_one(obj_key)
        except:
            raise UserError(_("MongoDB Error\nCan't connect with the server on %s") % (MONGODB_URL))

    def __filter_obj_data(self, vals=None):
        # Si obj_data es un diccionario
        if self.obj_data and type(self.obj_data) is dict:
            # Eliminar campos que no se modificaron
            for field, value in self.obj_data.items():
                # Si se estableció vals es una actualización,
                # quitamos los campos que no cambiaron
                if vals and field not in vals:
                    del self.obj_data[field]
                # Si es un campo Unicode lo pasamos a UTF-8
                elif type(value) is unicode:
                    self.obj_data[field] = unidecode(value)

    def __must_notify(self, is_notifiable, fields_to_watch=None, vals=None):
        if not is_notifiable(self):
            return False
        # Return true if have fields to watch
        if fields_to_watch and vals:
            return len(set(vals).intersection(set(fields_to_watch))) > 0
        # Watch all by default
        return True

    def __google_pubsub_send(self, action, topic='PUBLIC-OUT'):
        # If collection and data are not empty
        if self.collection and self.obj_data:
            try:
                # Create full cualified topic path
                topic_path = publisher.topic_path(os.environ['GOOGLE_CLOUD_PROJECT_ID'], topic)
                # Publish message
                publish = publisher.publish(topic_path, object=str(self.collection), data=str(self.obj_data).encode('base64'), id=str(self.obj_id), action=str(action.upper()))
                # Debug output
                OutputHelper.print_text("- oper_type: {}"
                                        "\n    - publish_result: {}"
                                        "\n    - obj_id: {}"
                                        "\n    - obj_type: {}"
                                        "\n    - obj_data: {}"
                                        .format(action.upper(), publish.result(), self.obj_id, self.collection, json.dumps(self.obj_data, indent=8, sort_keys=True)), MsgTypes.OK)
            except:
                raise UserError(_("Google Pub/Sub Error\nCan't send data to Google servers!"))

    def __b2b_record(self, mode='create', vals=None):  
        # Obtener los objetos configurados
        send_items = self.env['b2b.item'].sudo().search([('mode', '=', 'send')])
        # Para cada elemento
        for si in send_items:
            # Ejecutamos el código con exec(si.code)
            # establece localmente las siguentes variables y métodos:
            #   fields_to_watch <type 'tuple'>
            #   is_notifiable <type 'function'>
            #   get_obj_data <type 'function'>
            exec(si.code)
            # Comprobamos si se debe notificar
            if self.__must_notify(is_notifiable, fields_to_watch, vals):
                # Obtenemos el id
                self.obj_id = self.id
                # Obtenemos el nombre
                self.collection = str(si.name)
                # Obtenemos los datos
                self.obj_data = get_obj_data(self)
                # Filtramos los datos
                self.__filter_obj_data(vals)
                # Actualizamos los datos en Mongo DB
                self.__update_on_mongodb(mode)
                # Si es un borrado o hay datos
                if mode == 'delete' or len(self.obj_data) > 0:
                    # Definido en la configuración del objeto
                    if send_to_clients:
                        # Obtener los clientes configurados (todos), aunque esté inactivo se le envían igualmente los mensajes
                        # para que al activarlo de nuevo no los pierda (hay que tener en cuenta que tienen una caducidad)
                        send_clients = self.env['b2b.client'].sudo().search(['|', ('active', '=', True), ('active', '=', False)])
                        # Enviar a cada cliente
                        for client in send_clients:
                            # Comprobar si está en la lista o es vip
                            if client.id in send_to_clients or client.vip:
                                # Enviamos el mensaje por privado
                                self.__google_pubsub_send(mode, client.ref)
                    else:
                        # Enviamos el mensaje a todos
                        self.__google_pubsub_send(mode)
                break

    # -------------------------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        item = super(BaseB2B, self).create(vals)
        item.__b2b_record('create', vals)
        return item

    @api.multi
    def write(self, vals):
        super(BaseB2B, self).write(vals)
        for item in self:
            item.__b2b_record('update', vals)
        return True

    @api.multi
    def unlink(self):
        for item in self:
            item.__b2b_record('delete')
        super(BaseB2B, self).unlink()
        return True
