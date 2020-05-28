# -*- coding: utf-8 -*-
from odoo import api, models, tools
from .helper import OutputHelper, JSync

# Module base class
class BaseB2B(models.AbstractModel):

	_inherit = 'base'

	@api.model
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

	@api.model
	def get_field_multicompany(self, field='name'):
		"""
		Get values for multicompany fields (only for )

		:param field: Field name string
		:return: list of tuples (company, record_id)

		Return example:
		[
			(res.company(5), 28),
			(res.company(8), 12)
		]
		"""
		result = list()
		res_id = '%s,%s' % (self._name, self.id)
		for value in self.env['ir.property'].with_context().sudo().search([('name', 'like', field), ('res_id', 'like', res_id)]):
			result_item = False
			if value.type == 'many2one':
				model, reg_id = value.value_reference.split(',')
				result_item = int(self.env[model].browse(reg_id).id)
			elif value.type == 'boolean':
				result_item = bool(value.value_integer)
			elif value.type == 'float':
				result_item = int(value.value_integer)
			elif value.type == 'text':
				result_item = str(value.value_text)
			elif value.type == 'binary':
				result_item = value.value_binary
			result.append((value.company_id, result_item))
		return result

	@api.multi
	def is_notifiable_check(self, mode='create', vals=None):
		"""
		Notifiable config items

		:param models: Item config models
		:param code: Item config code
		:param vals: Default model data update dict (to check fields)
		:return: boolean
		"""
		b2b_items_out = self.env['b2b.item.out'].search([])
		for record in self:
			items_list = list()
			for item in b2b_items_out:
				item_models = [x.strip() for x in item.model.split(',')]
				if record._name in item_models and type(item.code) is unicode:
					b2b = dict()

					# Ejecutamos el código con exec(item.code)
					# establece en la variable local b2b los siguientes atributos:
					#   b2b['fields_to_watch'] <type 'tuple'>
					#   b2b['is_notifiable'] <type 'function'>
					#   b2b['pre_data'] <type 'function'> ¡No usado aquí! ¡Opcional!
					#   b2b['get_data'] <type 'function'> ¡No usado aquí!
					#   b2b['pos_data'] <type 'function'> ¡No usado aquí! ¡Opcional!
					exec(item.code, locals(), b2b)

					# Si este registro es notificable
					if b2b['is_notifiable'](record, mode, vals):
						if type(b2b['fields_to_watch']) in (list, tuple) and type(vals) is dict:
							# Si se están actualizando campos notificables
							if bool(set(vals).intersection(set(b2b['fields_to_watch']))):
								items_list.append(item.name)
						else:
							items_list.append(item.name)

			# All notifiable items
			return items_list

	@api.model
	def b2b_record(self, mode, vals=None, conf_items_before=None):
		packets = []
		jsync_conf = self.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error', 'packet_size', 'base_url'])
		conf_items_after = self.is_notifiable_check(mode, vals)
		for item in self.env['b2b.item.out'].search([('name', 'in', conf_items_before or conf_items_after)]):
			import datetime
			import base64

			b2b = dict()
			b2b['images_base'] = jsync_conf['base_url']
			# Ejecutamos el código con exec(item.code)
			# establece en la variable local b2b los siguientes atributos:
			#   b2b['fields_to_watch'] <type 'tuple'> ¡No usado aquí!
			#   b2b['is_notifiable'] <type 'function'> ¡No usado aquí!
			#   b2b['pre_data'] <type 'function'> ¡Opcional!
			#   b2b['get_data'] <type 'function'>
			#   b2b['pos_data'] <type 'function'> ¡Opcional!
			exec(item.code, locals(), b2b)

			# No se puede buscar dentro de un None
			if conf_items_before is None:
				conf_items_before = list()
			# Si antes era notificable y ahora no lo eliminamos
			if mode and item.name in conf_items_before and item.name not in conf_items_after:
				mode = 'delete'
			# Si antes no era notificable y ahora si lo creamos (ponemos vals a none para que se envíe todo)
			elif mode and item.name not in conf_items_before and item.name in conf_items_after:
				mode = 'create'
				vals = None

			# Creamos un paquete
			packet = JSync(settings=jsync_conf)
			# Obtenemos el modo
			packet.mode = mode
			# Obtenemos el nombre
			packet.name = item.name

			# Ejecutamos la función pre_data si existe
			if 'pre_data' in b2b and callable(b2b['pre_data']):
				b2b['pre_data'](self, mode)

			# Obtenemos los datos
			packet.data = b2b['get_data'](self)
			# Filtramos los datos
			packet.filter_data(vals)
			# Guardamos el paquete
			packets.append(packet)

			# Lo enviamos si procede
			if vals != False:
				if packet.send():
					item_id = '[PACKET]'
					if packet.data and type(packet.data) is dict:
						item_id = packet.data.get('jim_id', self.id)
					self.env.user.notify_info('[B2B] %s <b>%s</b> %s' % (mode.capitalize(), packet.name, item_id))

			# Ejecutamos la función pos_data si existe
			if 'pos_data' in b2b and callable(b2b['pos_data']):
				b2b['pos_data'](self, mode)

		# Paquetes a enviar
		return packets

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.model
	def create(self, vals):
		#print("----------- [B2B BASE] CREATE", self._name, vals)
		item = super(BaseB2B, self).create(vals)
		if item._name != 'product.template':
			item.b2b_record('create')
		return item

	@api.multi
	def write(self, vals):
		#print("----------- [B2B BASE] WRITE", self._name, vals)
		items_to_send = self.is_notifiable_check('update', vals)
		super(BaseB2B, self).write(vals)
		for item in self:
			item.b2b_record('update', vals, conf_items_before=items_to_send)
		return True

	@api.multi
	def unlink(self):
		#print("----------- [B2B BASE] DELETE", self._name, self)
		packets = list()
		for item in self:
			packets += item.b2b_record('delete', False, conf_items_before=item.is_notifiable_check('delete'))
		if super(BaseB2B, self).unlink():
			for packet in packets:
				if packet and packet.send():
					item_id = '[PACKET]'
					if packet.data and type(packet.data) is dict:
						item_id = packet.data.get('jim_id', self.id)
					self.env.user.notify_info('[B2B] Delete <b>%s</b> %s' % (packet.name, item_id))
		return True