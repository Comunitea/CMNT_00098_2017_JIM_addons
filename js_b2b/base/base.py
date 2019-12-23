# -*- coding: utf-8 -*-
from odoo import api, fields, models
from .helper import JSync
import os

# Module base class
class BaseB2B(models.AbstractModel):
    _inherit = 'base'

    def __must_notify(self, is_notifiable, fields_to_watch=None, vals=None):
        if not is_notifiable(self):
            return False
        # Return true if have fields to watch
        if fields_to_watch and vals:
            return len(set(vals).intersection(set(fields_to_watch))) > 0
        # Watch all by default
        return True

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
                item = JSync(self.id)
                # Obtenemos el nombre
                item.obj_type = str(si.name)
                # Obtenemos los datos
                item.obj_data = get_obj_data(self)
                # Enviamos los datos
                return item.send('', mode)
        return False

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

