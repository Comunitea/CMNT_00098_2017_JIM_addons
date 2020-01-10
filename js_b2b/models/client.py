# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from ..base.helper import JSync

class B2bClients(models.Model):
	_name = 'b2b.client'
	_description = "B2B Client"
	_rec_name = 'partner'

	partner = fields.Many2one('res.partner', 'Odoo Client', ondelete='cascade', required=True, help="Select a client")
	ctype = fields.Selection(selection=[('premium', 'Premium'),('vip', 'VIP')], string='Special Type', help="Premium: Enable to receive premium items\nVIP: Receive all data, not only yours") 
	iam_sa = fields.Char('Service Account', required =False, translate=False, help="Google IAM service account")
	iam_key = fields.Binary('Service Account Key', attachment=True, help="Google IAM service account key")
	send = fields.Boolean('Can Send', default=False, help="Authorize this client for send data items")
	active = fields.Boolean('Active', default=True, help="Enable or disable this client")
	items = fields.Many2many('b2b.item', 'b2b_client_item_rel', string='Data Items')

	def __b2b_record(self, mode='create', vals=None):  
		jitem = JSync(self.id)
		# Set data
		jitem.obj_name = 'client'
		jitem.obj_data = {
			'partner:partner_id': self.partner.id,
			'fixed:partner_ref': self.partner.ref,
			'fixed:partner_name': self.partner.name,
			'fixed:iam_sa': self.iam_sa,
			'iam_key': self.iam_key,
			'ctype:type': self.ctype,
			'send': self.send,
			'active': self.active
		}
		# Filter data
		jitem.filter_obj_data(vals)
		# Send item
		return jitem.send('config', mode, 300)

	# -------------------------------------------------------------------------------------------

	@api.multi
	def toggle_send(self):
		for client in self:
			client.send = not client.send

	@api.model
	def create(self, vals):
		client = super(B2bClients, self).create(vals)
		result = client.__b2b_record('create')
		client.iam_sa = result.get('iam_sa', False)
		client.iam_key = result.get('iam_key', False)
		return client

	@api.multi
	def write(self, vals):
		super(B2bClients, self).write(vals)
		for client in self:
			client.__b2b_record('update', vals)
		return True

	@api.multi
	def unlink(self):
		for client in self:
			client.__b2b_record('delete', False)
		super(B2bClients, self).unlink()
		return True