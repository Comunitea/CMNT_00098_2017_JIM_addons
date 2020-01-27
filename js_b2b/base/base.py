# -*- coding: utf-8 -*-
from odoo import api, models
from .helper import JSync

# Module base class
class BaseB2B(models.AbstractModel):
	_inherit = 'base'

	def get_field_translations(self, field='name'):
		"""
		Get field translations dict for all models

		:param field: Field name string
		:return: dict (ISO 639-1 + '-' + ISO 3166-1 Alpha-2)

		Return example:
		{
			'en-EN': 'Test',
			'es-ES': 'Prueba'
		}
		"""
		field_name = ','.join([self._name, field])
		configured_langs = self.env['res.lang'].search([('active', '=', True), ('translatable', '=', True)])
		# Default values
		translations = { lang.code.replace('_', '-'):self[field] or None for lang in configured_langs }
		# Query to get translations
		self._cr.execute("SELECT lang, value FROM ir_translation WHERE type='model' AND name=%s AND res_id=%s", (field_name, self.id))
		# Update translations dict
		translations.update({ lang_code:field_translation for lang_code,field_translation in self._cr.fetchall() })
		# Return lang -> str dict
		return translations

	def __must_notify(self, model, fields_to_watch=None, vals=None):
		"""
		Check if this model and item is notifiable 

		:param fields_to_watch: Fields to watch tuple
		:param vals: Default model data update dict (to check fields)
		:return: boolean
		"""
		if not self._name == model:
			return False
		# Return true if have fields to watch
		if type(fields_to_watch) is tuple and type(vals) is dict:
			return bool(set(vals).intersection(set(fields_to_watch)))
		# Watch all by default
		return True

	def __b2b_record(self, mode='create', vals=None):
		"""
		Private method to check configured items and send the data

		:param mode: String, CRUD mode
		:param vals: Default model data update dict (to check changes)
		:return: boolean
		"""
		send_items = self.env['b2b.item'].sudo().search([])
		# Para cada elemento activo
		for item in send_items:
			# Comprobamos si se debe notificar
			item_data = item.must_notify(self, vals)
			if item_data:
				# Obtenemos el id
				packet = JSync(self.id)
				# Obtenemos el nombre
				packet.name = item.name
				# Obtenemos los destinatarios
				packet.dest = item.clients.ids if item.clients else list()
				# Obtenemos los datos
				packet.data = item_data
				# Normalizamos los datos
				packet.filter_data(vals)
				if not mode:
					# Devolvemos el paquete 
					# para enviarlo más tarde
					return packet
				else:
					# Enviamos los datos si son correctos
					if mode == 'delete' or packet.data:
						return packet.send(action=self.mode)
					return False
		return False

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		item = super(BaseB2B, self).create(vals)
		item.__b2b_record('create')
		return item

	@api.multi
	def write(self, vals):
		super(BaseB2B, self).write(vals)
		for item in self:
			item_active = vals.get('active')
			item_status = vals.get('state')
			# Al activarse y no estar cancelado se crea de nuevo
			if item_active is True and item_status != 'cancel':
				item.__b2b_record('create')
			# Al desactivarse o cancelarse se elimina
			elif item_active is False or item_status == 'cancel':
				item.__b2b_record('delete', False)
			# Para otros cambios se actualiza (si está activo)
			elif item_active in (True, None):
				item.__b2b_record('update', vals)
		return True

	@api.multi
	def unlink(self):
		packets = []
		for item in self:
			packets.append(item.__b2b_record(False, False))
		if super(BaseB2B, self).unlink():
			for packet in packets:
				if packet:
					packet.send(action='delete')
		return True