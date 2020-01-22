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
		:return: dict

		Return example:
		{
			'en_EN': 'Test',
			'es_ES': 'Prueba'
		}
		"""
		field_name = ','.join([self._name, field])
		configured_langs = self.env['res.lang'].search([('translatable', '=', True)])
		# Default values
		translations = { lang.code:self[field] or None for lang in configured_langs }
		# Query to get translations
		self._cr.execute("SELECT lang, value FROM ir_translation WHERE type='model' AND name=%s AND res_id=%s", (field_name, self.id))
		# Update translations dict
		translations.update({ lang_code:field_translation for lang_code,field_translation in self._cr.fetchall() })
		# Return lang -> str dict
		return translations

	def __must_notify(self, fields_to_watch=None, vals=None):
		"""
		Check if this model and item is notifiable 

		:param fields_to_watch: Fields to watch tuple
		:param vals: Default model data update dict (to check fields)
		:return: boolean
		"""
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
		self.b2b_id = self.id
		self.b2b_mode = mode
		send_items = self.env['b2b.item'].sudo().search([])
		# Para cada elemento activo
		for si in send_items:
			# Ejecutamos el código con exec(si.code)
			# establece globalmente las siguentes variables y métodos:
			#   fields_to_watch <type 'tuple'>
			#   is_notifiable <type 'function'>
			#   get_data <type 'function'>
			exec(si.code, globals())
			# Comprobamos si se debe notificar
			if is_notifiable(self, vals) and self.__must_notify(fields_to_watch, vals):
				# Obtenemos el id
				item = JSync(self.b2b_id)
				# Obtenemos el nombre
				item.obj_name = str(si.name)
				# Obtenemos los destinatarios
				item.obj_dest = si.clients.ids if si.clients else list()
				# Obtenemos los datos
				if self.b2b_mode != 'delete':
					item.obj_data = get_data(self)
					# Filtramos los datos
					# para eliminar los que no cambiaron
					# o no son fixed
					item.filter_obj_data(vals)
				# Enviamos los datos si son correctos
				# es un borrado o obj_data no puede estar vacío
				if self.b2b_mode == 'delete' or item.obj_data or item.obj_images:
					return item.send('', self.b2b_mode)
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
				item.__b2b_record('create', vals)
			# Al desactivarse o cancelarse se elimina
			elif item_active is False or item_status == 'cancel':
				item.__b2b_record('delete', False)
			# Para otros cambios se actualiza (si está activo)
			elif item_active in (True, None):
				item.__b2b_record('update', vals)
		return True

	@api.multi
	def unlink(self):
		for item in self:
			item.__b2b_record('delete', False)
		super(BaseB2B, self).unlink()
		return True