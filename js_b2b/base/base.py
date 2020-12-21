# -*- coding: utf-8 -*-
from odoo import api, models, tools
from .helper import Subprocess, JSync
from base64 import b64encode
import logging

# Este es el vigilante que lanza las comprobaciones sobre los registros que se están modificando
# podemos utilizar with_context(b2b_evaluate=False) para que no se ejecuten las funciones de este modelo

_logger = logging.getLogger('B2B-BASE')

# Module base class
class BaseB2B(models.AbstractModel):

	_inherit = 'base'

	@api.model
	def get_field_translations(self, field='name'):
		"""
		Get field translations dict for active langs on all models

		:param field: Field name string
		:return: dict (ISO 639-1 + '-' + ISO 3166-1 Alpha-2)

		Return example:
		{
			'en-EN': 'Test',
			'es-ES': 'Prueba'
		}
		"""
		origin = self.with_context(lang='en_US')
		# Field name search string
		field_name = ','.join([self._name, field])
		# Search active langs but skip 'es'
		configured_langs = self.env['res.lang'].search([('active', '=', True), ('translatable', '=', True), ('code', '!=', 'es')])
		# Default values
		translations = { lang.code.replace('_', '-'):origin[field] or None for lang in configured_langs }
		# Query to get translations
		self._cr.execute("SELECT lang, value FROM ir_translation WHERE type='model' AND name=%s AND res_id=%s", (field_name, self.id))
		# Update translations dict
		translations.update({ lang_code.replace('_', '-'):field_translation for lang_code, field_translation in self._cr.fetchall() if lang_code.replace('_', '-') in translations })
		# Return lang -> str dict
		return translations

	@api.model
	def get_base64_report_pdf(self, model_name):
		"""
		Get PDF document as base64 string

		:param model_name: Report model name string
		:return: base64
		"""
		ctx = self.env.context.copy()
		ctx.pop('default_type', False)
		# Necesitamos quitar la variable default_type del contexto
		# de las facturas para que no de error el tipo en ir.attachment
		# https://github.com/odoo/odoo/issues/15279
		docfile = self.env['report'].with_context(ctx).get_pdf([self.id], model_name)
		return b64encode(docfile)

	@api.model
	def get_field_multicompany(self, field='name'):
		"""
		Get values for multicompany fields

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
		for value in self.env['ir.property'].sudo().search([('name', '=', field), ('res_id', '=', res_id)]):
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
	def on_jsync(self):
		"""
		Checks if record is alredy on JSync

		:return: boolean
		"""
		self.ensure_one()
		res_id = '%s,%s' % (self._name, self.id)
		export_found = self.env['b2b.export'].search([('res_id', '=', res_id)], limit=1)
		return True if export_found else False

	@api.multi
	def auto_mode(self, object_str, conf_after):
		# Determinamos el modo correcto en actualizaciones
		if conf_items_before and mode == 'update':
			# No se puede buscar dentro de un None
			if conf_items_before is None:
				conf_items_before = list()
			# Si antes era notificable y ahora no lo eliminamos
			if item.name in conf_items_before.keys() and item.name not in conf_items_after.keys():
				b2b['crud_mode'] = 'delete'
			# Si antes no era notificable y ahora si o lo creamos
			elif (item.name not in conf_items_before.keys() and item.name in conf_items_after.keys()) or not self.on_jsync():
				b2b['crud_mode'] = 'create'

	@api.multi
	def is_notifiable_check(self, mode='create', vals=dict()):
		"""
		Notifiable config items

		:param models: Item config models
		:param code: Item config code
		:param vals: Default model data update dict (to check fields)
		:return dict: Record applicable configs
		"""
		items_dict = dict()
		jsync_conf = self.env['b2b.settings'].get_default_params(['base_url', 'docs_after'])
		b2b_config = self.env['b2b.item.out'].search([('active', '=', True), ('model', 'like', '%%%s%%' % self._name)])

		# Vals siempre como dict
		if type(vals) is not dict:
			vals = dict()

		for item in b2b_config:
			# Comprobar que el modelo coincide exactamente ya que con el filtro anterior
			# en el search() no es suficiente (ej: customer y customer.address)
			if self._name in item.get_models() and type(item.code) is unicode:
				b2b = item.evaluate(mode, jsync_conf)

				# Campos vigilados
				watched_fields = b2b.get('fields_to_watch')
				# Datos actuales en el registro
				record_data = self.read(watched_fields)[0] or dict()
				# Datos cambiados (realmente)
				changed_fields = { k : vals[k] for k in vals if k in record_data and vals[k] != record_data[k] }
				# Sólo enviar updates si hay un cambio en los datos
				change_allowed = bool(mode in ('create', 'delete', 'replace') or changed_fields)

				# Si este registro es notificable
				if b2b['is_notifiable'](self, mode, vals):

					# Si se restringen los campos a enviar
					if changed_fields and type(watched_fields) in (list, tuple):

						# Si se están actualizando campos notificables
						items_dict.update({ item.name: bool(set(vals).intersection(set(watched_fields))) })

					else:

						# Si watched_fields es None o vals está vacío
						items_dict.update({ item.name: change_allowed })

		# All notifiable items
		return items_dict

	@api.multi
	def b2b_record(self, mode, vals=None, conf_items_before=None, auto_send=True, user_notify=True, sub_methods=True):
		"""
		B2B Action Trigger

		:param mode: Real action
		:param vals: Values to update
		:param conf_items_before: Applicable configs before action
		:param auto_send: Send packets after creation
		:param user_notify: Show user notification (Marta dijo que mejor que no saliese)
		:param sub_methods: Call pre_data & pos_data
		:return: JSync Packet
		"""
		packets = list()
		conf_items_after = self.is_notifiable_check(mode, vals)
		applicable_configs = conf_items_before or conf_items_after
		importing_file = self.env.context.get('import_file', False)
		b2b_config = self.env['b2b.item.out'].search([('name', 'in', applicable_configs.keys())])

		# Tiene una configuración activa y no se está
		# haciendo una importación
		if applicable_configs and not importing_file:

			jsync_conf = self.env['b2b.settings'].get_default_params()
			importing_file = self.env.context.get('import_file', False)
			_logger.info("Configuración aplicable: %s", applicable_configs)

			for item in b2b_config:
				# Configuration eval
				b2b = item.evaluate(mode, jsync_conf)
				b2b['crud_mode'] = mode

				# Determinamos el modo correcto en actualizaciones
				if mode == 'update':
					# No se puede buscar dentro de un None
					if conf_items_before is None:
						conf_items_before = list()
					# Si antes era notificable y ahora no lo eliminamos
					if item.name in conf_items_before.keys() and item.name not in conf_items_after.keys():
						b2b['crud_mode'] = 'delete'
					# Si antes no era notificable y ahora si o lo creamos
					elif (item.name not in conf_items_before.keys() and item.name in conf_items_after.keys()) or not self.on_jsync():
						if self.on_jsync(): applicable_configs.update({ item.name: True })
						b2b['crud_mode'] = 'create'

				# Restringir cambios no reales. Ej: product_id.write({ 'name': self.name })
				if applicable_configs.get(item.name, False):
					# Creamos un paquete
					packet = JSync(self.env, settings=jsync_conf)
					# ID del registro
					packet.id = self.id
					# Modelo del registro
					packet.model = self._name
					# Obtenemos el nombre
					packet.name = item.name
					# Obtenemos la copia del modo
					packet.mode = b2b['crud_mode']

					_logger.info("Paquete para [%s,%i] en modo [%s]" % (packet.model, packet.id, b2b['crud_mode']))

					# Obtenemos la relacción (si la tiene)
					if 'related_to' in b2b and callable(b2b['related_to']):
						packet.related = b2b['related_to'](self, mode)

					# Ejecutamos la función pre_data si existe y sub_methods es True
					if sub_methods and 'pre_data' in b2b and callable(b2b['pre_data']):
						b2b['pre_data'](self, mode)

					# Obtenemos los datos
					packet.data = b2b['get_data'](self, mode)
					# Filtramos los datos
					packet.filter_data(b2b['crud_mode'])
					# Si procede enviamos el paquete
					if auto_send: packet.send(notify=user_notify)
					# Guardamos el paquete
					packets.append(packet)

					# Ejecutamos la función pos_data si existe y sub_methods es True
					if sub_methods and 'pos_data' in b2b and callable(b2b['pos_data']):
						Subprocess(self).add(b2b['pos_data'], self, mode)

		# Paquetes a enviar
		return packets

	# ------------------------------------ OVERRIDES ------------------------------------

	@api.multi
	def get_metadata(self):
		"""
		Sets B2B Notifiable data on system metadata debug modal

		:return: list of dicts
		"""
		metadata = super(BaseB2B, self).get_metadata()
		for i,v in enumerate(metadata):
			record = self.browse(v['id'])
			record_on_jsync = record.on_jsync()
			record_notifiable = record.is_notifiable_check()
			metadata[i]['b2b_notifiable'] = ', '.join(record_notifiable) if record_notifiable else 'false'
			metadata[i]['b2b_record_on_jsync'] = 'true' if record_on_jsync else 'false'
		return metadata

	@api.model
	def create(self, vals):
		"""
		Overwrite to call B2B create actions

		Set context var b2b_evaluate=False to skip
		"""
		item = super(BaseB2B, self).create(vals)
		if item and self.env.context.get('b2b_evaluate', True):
			item.b2b_record('create')
		return item

	@api.multi
	def write(self, vals):
		"""
		Overwrite to call B2B write actions

		Set context var b2b_evaluate=False to skip
		"""
		b2b_evaluate = self.env.context.get('b2b_evaluate', True)
		for record in self:
			if b2b_evaluate:
				items_to_send = record.is_notifiable_check('update', vals)
			if b2b_evaluate and super(BaseB2B, record).write(vals):
				record.b2b_record('update', vals, conf_items_before=items_to_send)
		return True

	@api.multi
	def unlink(self):
		"""
		Overwrite to call B2B unlink actions

		Set context var b2b_evaluate=False to skip
		"""
		b2b_evaluate = self.env.context.get('b2b_evaluate', True)
		for record in self:
			if b2b_evaluate:
				packets = record.b2b_record('delete', auto_send=False)
			if b2b_evaluate and super(BaseB2B, record).unlink():
				for packet in packets:
					packet.send(notify=True)
		return True