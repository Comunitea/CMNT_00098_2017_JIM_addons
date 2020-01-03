# -*- coding: utf-8 -*-
from odoo import api, fields, models
from .helper import JSync

# Module base class
class BaseB2B(models.AbstractModel):
	_inherit = 'base'

	def get_field_translations(self, field='name'):
		field_name = ','.join([self._name, field])
		configured_langs = self.env['res.lang'].search([('translatable', '=', True)])
		# Default values
		translations = { lang.code:self[field] for lang in configured_langs }
		# Query to get translations
		self._cr.execute("SELECT lang, value FROM ir_translation WHERE type='model' AND name=%s AND res_id=%s", (field_name, self.id))
		# Update translations dict
		translations.update({ lang_code:field_translation for lang_code,field_translation in self._cr.fetchall() })
		# Return lang -> str dict
		return translations

	def __must_notify(self, is_notifiable, fields_to_watch=None, vals=None):
		# Check if model is not notifiable
		if not is_notifiable(self):
			return False
		# Return true if have fields to watch
		if fields_to_watch and vals:
			return len(set(vals).intersection(set(fields_to_watch))) > 0
		# Watch all by default
		return True

	def __b2b_record(self, mode='create', vals=None):
		# Obtener los objetos configurados
		send_items = self.env['b2b.item'].sudo().search([])
		# Para cada elemento
		for si in send_items:
			# Ejecutamos el código con exec(si.code)
			# establece localmente las siguentes variables y métodos:
			#   fields_to_watch <type 'tuple'>
			#   is_notifiable <type 'function'>
			#   send_to <type 'function'>
			#   get_data <type 'function'>
			exec(si.code)
			# Comprobamos si se debe notificar
			if self.__must_notify(is_notifiable, fields_to_watch, vals):
				# Obtenemos el id
				item = JSync(self.id)
				# Obtenemos el nombre
				item.obj_type = str(si.name)
				# Para quien es (False para todos)
				item.obj_to = send_to(self)
				# Obtenemos los datos
				item.obj_data = get_data(self)
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

