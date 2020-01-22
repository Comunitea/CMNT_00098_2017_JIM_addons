# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync
import re

class B2bItems(models.Model):
	_name = 'b2b.item'
	_description = 'B2B Item'
	_order = 'sequence, id'
	_default_code_str = re.sub(r'(^[ ]{0,8})', '', """
        # Set to None for watch all
        fields_to_watch = ('name', 'reference')
        
        def is_notifiable(self, vals):
            return self._name == 'product.product'

        def get_data(self):
            return {
                # Sends names dict when field has changed
                'name': self.get_field_translations('name'),
                # fixed: modifier forces send even if it has not changed
                'fixed:reference': self.default_code,
                # field: modifier sends if field has changed, if not setted send null
                'categ_id:category_id': self.categ_id.id if self.categ_id else None,
                # image: modifier uploads base64 image to public server and replaces this param with the URL
                'image:logo': '/9j/4AAQSkZJRgABAQAAAQABAAD...'
            }
	""", flags=re.M).strip()

	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name")
	description = fields.Char('Description', required=False, translate=False, help="Set the item description")
	clients = fields.Many2many('b2b.client', 'b2b_client_item_rel', 'b2b_item_id', 'b2b_client_id')
	code = fields.Text('Code', required=True, translate=False, default=_default_code_str, help="Write the item code")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")
	sequence = fields.Integer(help="Determine the items order")

	@staticmethod
	def __check_code(code):
		if type(code) is unicode:
			# Exec B2B Item Code
			try:
				exec(code, globals())
			except Exception as e:
				raise UserError(_('Syntax Error!\n') + str(e))
			# Check required vars and methods to avoid errors
			variables = { 'fields_to_watch': tuple }
			methods = ['is_notifiable', 'get_data']
			for var in tuple(variables.keys() + methods):
				if not var in locals():
					raise UserError(_('Code Error!\n %s not defined' % (var)))
			for var, typ in variables.items():
				if type(eval(var)) is not typ:
					raise UserError(_('Code Error!\n %s must be a %s' % (var, typ)))
			for method in methods:
				if not callable(eval(method)):
					raise UserError(_('Code Error!\n %s must be a function' % (method)))