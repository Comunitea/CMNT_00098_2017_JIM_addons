# -*- coding: utf-8 -*-
from odoo import api, models
from odoo.exceptions import UserError
from .helper import MsgTypes, OutputHelper
from pulsar import Client, MessageId, AuthenticationToken
from pulsar.schema import Record, String, Map, JsonSchema
from unidecode import unidecode
import json

# Constants definition
APULSAR_PRN = 'Odoo-B2B-Module'
APULSAR_URL = 'pulsar://192.168.1.207:6650/'
APULSAR_TOK = 'eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiJtYXN0ZXIifQ.1bPrM620MbNdAVOZYepUnqYwDAG0SaPPMFfNNXMlr_8' # "master" Role Key
APULSAR_ERR = "Apache Pulsar Error!\nCan't connect with the server on %s or queue limit reached" % (APULSAR_URL)

# Init Apache Pulsar
pcli = Client(APULSAR_URL, authentication=AuthenticationToken(APULSAR_TOK))

# Exchange data validation schema
class ExchangeData(Record):
    action = String()
    data = Map(String())

# Module base class
class BaseB2B(models.AbstractModel):
    _inherit = 'base'

    obj_data = None # Item data dict
    collection = None # Pulsar topic

    def __filter_obj_data(self, vals=None):
        # Si obj_data es un diccionario
        if self.obj_data and type(self.obj_data) is dict:
            # Eliminar campos que no se modificaron
            for field, value in self.obj_data.items():
                # Si se estableció vals es una actualización,
                # quitamos los campos que no cambiaron y el id
                if vals and field not in vals and field != 'id':
                    del self.obj_data[field]
                # En caso contrario es un borrado, solo dejamos el id
                elif not vals and field != 'id':
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

    def __apache_pulsar_send(self, action):
        # If collection and data are not empty
        if self.collection and self.obj_data:
            try:
                # Create or use producer
                pulsar_producer = pcli.create_producer(
                    topic=self.collection,
                    schema=JsonSchema(ExchangeData),
                    producer_name=APULSAR_PRN,
                    block_if_queue_full=True,
                    batching_enabled=True,
                    batching_max_publish_delay_ms=10
                )
                # Send in async mode (queue)
                pulsar_producer.send_async(ExchangeData(action=action, data=self.obj_data), None)
                # End connection
                pulsar_producer.close()
                # Debug output
                OutputHelper.print_text("- oper_type: {}"
                                        "\n    - obj_type: {}"
                                        "\n    - obj_data: {}"
                                        .format(action.upper(), self.collection, json.dumps(self.obj_data, indent=8, sort_keys=True)), MsgTypes.OK)
            except:
                raise UserError(APULSAR_ERR)

    def _b2b_record(self, type='create', vals=None):
        send_items = self.env['b2b.item'].sudo().search([
            ('type', '=', 'send'),
            ('active', '=', True)
        ])

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
                # Obtenemos el nombre
                self.collection = str(si.name)
                # Obtenemos los datos
                self.obj_data = get_obj_data(self)
                # Filtramos los datos
                self.__filter_obj_data(vals)
                # Si no es un borrado pero no hay datos no enviamos nada
                if type == 'delete' or len(self.obj_data) > 1:
                    # Enviamos el mensaje por Pulsar
                    self.__apache_pulsar_send(type)

    # -------------------------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        item = super(BaseB2B, self).create(vals)
        item._b2b_record('create', vals)
        return item

    @api.multi
    def write(self, vals):
        super(BaseB2B, self).write(vals)
        for item in self:
            item._b2b_record('update', vals)
        return True

    @api.multi
    def unlink(self):
        for item in self:
            item._b2b_record('delete')
        super(BaseB2B, self).unlink()
        return True
