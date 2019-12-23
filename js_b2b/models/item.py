# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync
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

        # Get model data for a item
        def get_obj_data(self):
            return { }
    """, flags=re.M).strip()

    name = fields.Char('Item Name', required=False, translate=False, help="Set the item name")
    mode = fields.Selection([('send', 'Send'), ('receive', 'Receive')], 'Select Mode', default='send', help="Select operation mode")
    code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
    active = fields.Boolean('Active', default=True, help="Enable or disable this item")

    @staticmethod
    def __check_code(code):
        if type(code) is unicode:
            # Exec B2B Item Code
            try:
                exec(code)
            except Exception as e:
                raise UserError(_('Syntax Error!\n') + str(e))
            # Check required methods to avoid errors
            if not 'fields_to_watch' in locals():
                raise UserError(_('Code Error!\n fields_to_watch not defined'))
            else:
                if fields_to_watch and not type(fields_to_watch) is tuple:
                    raise UserError(_('Code Error!\n fields_to_watch must be a tuple'))
            if not 'is_notifiable' in locals():
                raise UserError(_('Code Error!\n is_notifiable not defined'))
            else:
                if not callable(is_notifiable):
                    raise UserError(_('Code Error!\n is_notifiable must be a function'))
            if not 'get_obj_data' in locals():
                raise UserError(_('Code Error!\n get_obj_data not defined'))
            else:
                if not callable(get_obj_data):
                    raise UserError(_('Code Error!\n get_obj_data must be a function'))

    def __b2b_record(self, mode='create', vals=None):  
        jitem = JSync()
        # Set data
        jitem.obj_id = self.id
        jitem.obj_type = 'item'
        jitem.obj_data = { 
            'name': vals.get('name', False), 
            'mode': vals.get('mode', False)
        }
        # Filter data
        jitem.filter_obj_data(vals)
        # Send item
        jitem.send('config', mode, 60)

    # -------------------------------------------------------------------------------------------

    @api.model
    def create(self, vals):
        self.__check_code(vals.get('code'))
        item = super(B2bItems, self).create(vals)
        item.__b2b_record('create', vals)
        return item

    @api.multi
    def write(self, vals):
        self.__check_code(vals.get('code'))
        super(B2bItems, self).write(vals)
        for item in self:
           item.__b2b_record('update', vals)
        return True

    @api.multi
    def unlink(self):
        for item in self:
            item.__b2b_record('delete')
        super(B2bItems, self).unlink()
        return True