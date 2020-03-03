# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError
from ..base.helper import JSync

class B2bItemsIn(models.Model):
	_name = 'b2b.item.in'
	_description = 'B2B Item In'
	_order = 'sequence, id'

	name = fields.Char('Item Name', required=True, translate=False, help="Set the item name")
	model = fields.Char('Model Name', required=True, translate=False, help="Odoo model name")
	description = fields.Char('Description', required=False, translate=False, help="Set the item description")
	active = fields.Boolean('Active', default=True, help="Enable or disable this item")
	sequence = fields.Integer(help="Determine the items order")

	@api.model
	def __check_model(self):
		"""
		Check if is a valid model
		"""
		try:
			self.env[self.model].search_count([])
		except Exception as e:
			raise UserError(_('Model not found!'))

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		"""
		Check model on create
		"""
		item = super(B2bItemsIn, self).create(vals)
		item.__check_model()
		return item

	@api.multi
	def write(self, vals):
		"""
		Check model on write
		"""
		super(B2bItemsIn, self).write(vals)
		for item in self:
			item.__check_model()
		return True
