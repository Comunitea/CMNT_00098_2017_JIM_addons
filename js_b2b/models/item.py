# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
import re

class B2bItems(models.Model):
    _name = 'b2b.item'
    _description = "B2B Item"

    _default_code_str = re.sub(r'(^[ ]{0,8})', '', """
        # Fields to watch for changes
        fields_to_watch = None

        # When this model is notifiable
        def is_notifiable(self):
            return self._name == 'res.partner'

        # Get model data for a item, id is required
        def get_obj_data(self):
            return {
                'id': self.id
            }
    """, flags=re.M).strip()

    name = fields.Char('Item Name', required=False, translate=False, help="Set the item name")
    type = fields.Selection([('send', 'Send'), ('receive', 'Receive')], 'Select Type', default='send', help="Select operation mode")
    code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
    active = fields.Boolean('Active', default=True, help="Enable or disable this item")

    @staticmethod
    def _check_code(code):
        if type(code) is unicode:
            # Ejecutamos el código
            try:
                exec(code)
            except Exception as e:
                raise UserError('Syntax Error!\n' + str(e))
            # Comprobamos que el código tenga los métodos necesarios
            if not 'fields_to_watch' in locals():
                raise UserError('Code Error!\n fields_to_watch not defined')
            else:
                if fields_to_watch and not type(fields_to_watch) is tuple:
                    raise UserError('Code Error!\n fields_to_watch must be a tuple')
            if not 'is_notifiable' in locals():
                raise UserError('Code Error!\n is_notifiable not defined')
            else:
                if not callable(is_notifiable):
                    raise UserError('Code Error!\n is_notifiable must be a function')
            if not 'get_obj_data' in locals():
                raise UserError('Code Error!\n get_obj_data not defined')
            else:
                if not callable(get_obj_data):
                    raise UserError('Code Error!\n get_obj_data must be a function')

    @api.model
    def create(self, vals):
        self._check_code(vals.get('code'))
        return super(B2bItems, self).create(vals)

    @api.multi
    def write(self, vals):
        self._check_code(vals.get('code'))
        super(B2bItems, self).write(vals)
        return True
