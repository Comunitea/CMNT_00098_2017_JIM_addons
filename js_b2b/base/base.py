# -*- coding: utf-8 -*-
from odoo import api, models, tools
from .helper import OutputHelper, JSync

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
		translations.update({ lang_code.replace('_', '-'):field_translation for lang_code, field_translation in self._cr.fetchall() })
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

	def __b2b_record(self, mode=None, vals=None):
		"""
		Private method to check configured items and send the data

		:param mode: String, CRUD mode
		:param vals: Default model data update dict (to check changes)
		:return: boolean
		"""
		packets = []
		send_items = self.env['b2b.item.out'].sudo().search([])
		# Para cada elemento activo
		for item in send_items:
			# Comprobamos si se debe notificar y recogemos los datos
			item_to_send = item.must_notify(self, mode, vals) or dict()
			# Acción a realizar
			item_action = item_to_send.get('action')
			# Datos a enviar
			item_data = item_to_send.get('data')
			# Si tiene acción y datos
			if item_action and item_data:
				# Obtenemos el id
				packet = JSync(self.id)
				# Obtenemos el nombre
				packet.name = item.name
				# Obtenemos los datos
				packet.data = item_data
				# Normalizamos los datos
				packet.filter_data(vals)
				# Guardamos el paquete
				packets.append(packet)
				# No se puede crear un elemento si se está llamando desde unlink()
				# esto solo pasará si hemos modificado la acción por defecto
				bad_action = item_action == 'create' and mode == False
				# Los datos no pueden estar vacíos, a no ser que se haga un borrado
				not_empty = item_action and item_action == 'delete' or packet.data
				# Si los datos son correctos lo enviamos
				if not_empty and not bad_action:
					packet.send(action=item_action)
					break
		# Paquetes creados
		return packets

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		print("----------- CREATE", self._name, vals)
		item = super(BaseB2B, self).create(vals)
		item.__b2b_record('create')
		return item

	@api.multi
	def write(self, vals):
		print("----------- WRITE", self._name, vals)
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
		print("----------- DELETE", self._name, self.id)
		packets = list()
		for item in self:
			packets += item.__b2b_record(False, False)
		if super(BaseB2B, self).unlink():
			for packet in packets:
				if packet:
					packet.send(action='delete')
		return True