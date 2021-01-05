# -*- coding: utf-8 -*-
from datetime import datetime
from requests import Session
from requests.adapters import HTTPAdapter
from odoo.exceptions import ValidationError
from requests.packages.urllib3.util.retry import Retry as httpRetry
from json import loads as json_load, dumps as json_dump
from unidecode import unidecode
from timeit import default_timer
from time import sleep
from odoo import api
from odoo.modules import registry
from concurrent.futures import ThreadPoolExecutor
import logging

_logger = logging.getLogger('B2B-OUTGOING')
_pool = ThreadPoolExecutor(max_workers=10)
_running = dict()

class Subprocess(object):

	__slots__ = ['_target', 'name']

	def __init__(self, target): 
		self._target = target

	def add(self, *args):
		self.name = '%s-%s' % (self._target._name, self._target.id)
		# If we are processing this record on other thread cancel
		# it first, if it's running can not be cancelled
		if self.name in _running:
			_running[self.name].cancel()
		# Schedule task
		_running[self.name] = _pool.submit(self.background_run, *args)

	def background_run(self, method, record, mode):
		"""
		Method to be called in a separate thread

		:param method: Object, method to call
		:param record: Object, record to notify
		:param mode: Str, CRUD mode
		"""

		# TODO: Probar esto ¿es mejor que la forma actual?
		# The test cursor prevents the use of another environnment while the current
		# transaction is not finished
		# from odoo.sql_db import TestCursor
		# if isinstance(self._target.env.cr, TestCursor):

		_logger.info("Ejecutando subproceso para [%s,%i]" % (record._name, record.id))

		while not self._target.env.cr.closed:
			# Wait while parent transaction ends
			_logger.debug("Esperando a que termine la opercaión actual...")
			sleep(2)

		# Now create a new cursor
		with api.Environment.manage():
			with self._target.pool.cursor() as new_cr:
				_logger.debug("Creado nuevo cursor para el subproceso...")
				# Autocommit ON
				new_cr.autocommit(True)

				try:
					# Fresh record
					record_issolated = record.with_env(record.env(cr=new_cr))
					# Call the method
					method(record_issolated, mode)
				except Exception as e:
					_logger.error(e)
				finally:
					_logger.info("Subproceso finalizado!")

class Chrono(object):

	__slots__ = ['name', 'start', 'end', 'elapsed']

	def __init__(self, name=None):
		self.name = name
		self.start = None
		self.end = None
		self.elapsed = None

	def __enter__(self):
		_logger.debug("Cronómetro: ON")
		self.start = default_timer()
		return self

	def __exit__(self,ty,val,tb):
		self.end = default_timer()
		self.elapsed = self.end - self.start
		_logger.debug("Cronómetro: OFF")

	def to_str(self):
		if self.elapsed:
			_logger.info("Medición: %.2fms" % self.elapsed)
			return "%.2fms" % self.elapsed
		return None

class JSync(object):

	__slots__ = ['id', 'env', 'model', 'mode', 'name', 'data', 'related', 'session', 'settings']

	def __init__(self, odoo_env, settings=None, retries=3):
		retry = httpRetry(total=retries, connect=retries, backoff_factor=0.3, status_forcelist=(500, 502, 504))
		adapter = HTTPAdapter(max_retries=retry)

		self.id = None # Record ID
		self.model = None # Record model name
		self.mode = 'create' # CRUD mode
		self.name = None # Data item name
		self.data = {} # Item data dict
		self.related = None # Odoo related model & record
		self.env = odoo_env # Odoo environment
		self.session = Session() # HTTP Session
		self.session.mount('http://', adapter)
		self.session.mount('https://', adapter)

		# If settings passed use it to avoid multiple calls
		self.settings = settings or self.env['b2b.settings'].get_default_params(fields=[
			'url', 
			'conexion_error', 
			'response_error'
		])

	def filter_data(self, crudMode=None, vals=None):
		"""
		Filter and normalizes item data (data)

		:param crudMode: Operation mode
		:return: dict

		data key modifiers:
			fixed:xxx -> Sends xxx always
		"""

		if self.data and type(self.data) is dict:
			for field, value in self.data.items():
				if ':' in field:

					# Before :
					modifier = field[:field.index(':')]
					# After :
					obj_new = field[field.index(':') + 1:]

					if modifier == 'fixed':
						# Replace key allways
						self.data[obj_new] = self.data.pop(field)
					elif modifier == 'changed' and (not vals or not obj_new in vals):
						# Delete if not changed
						del self.data[field]

				elif crudMode == 'delete' and field != 'jim_id':
					# Delete all except jim_id on delete
					del self.data[field]
				elif type(value) is list:
					# Convert lits to tuples
					self.data[field] = tuple(value)
				elif type(value) is unicode:
					# Decode unicode str's to utf-8
					self.data[field] = value.strip().decode('utf-8', 'replace')

		_logger.debug("Datos normalizados %s" % self.data)
		return self.data

	def can_send(self):
		"""
		Sends data to JSync server and prints on screen

		:return [bool (Send flag), str (Record model and ID string), object ()]
		"""

		RECORD_SEND = False
		EXPORT_ID = False
		RES_ID = '%s,%s' % (self.model, self.id)
		
		_logger.debug("¿Enviamos el paquete? Defecto: %s" % RECORD_SEND)

		# Comprobamos los datos necesarios
		# todos los mensajes tienen que tener por lo menos una clave primaria (jim_id)
		# la única excepción es cuando se elimina un registro que puede llevar sólo la clave
		if self.name and self.mode and (self.mode == 'delete' or len(self.data) > 1):
			# Check with new cursor
			with api.Environment.manage():
				with registry.RegistryManager.get(self.env.cr.dbname).cursor() as new_cr:
					new_cr.autocommit(True)
					env = api.Environment(new_cr, self.env.uid, self.env.context)

					# Check if record is synced with JSync
					EXPORT_ID = env['b2b.export'].search([('res_id', '=', RES_ID)], limit=1).id

					# Send the record comparing internal table reference?
					RECORD_SEND = bool(self.mode in ('create', 'update') or (EXPORT_ID and self.mode == 'delete'))

					# Log JSync record status
					_logger.debug("Registro en JSync: %s" % EXPORT_ID)

					# Is related record notifiable?
					if RECORD_SEND and self.related:
						_logger.debug("Relaccionado con: %s" % self.related)
						record_model, record_id = self.related.split(',')
						# Do not send the record if the related item is no longer notifiable
						if not env[record_model].browse(int(record_id)).is_notifiable_check():
							_logger.warning("El registro relaccionado ha invalidado el paquete!")
							RECORD_SEND = False

		return RECORD_SEND, RES_ID, EXPORT_ID

	def send(self, timeout_sec=30, notify=True, **kwargs):
		"""
		Sends data to JSync server and prints on screen

		:param action: CRUD action
		:param timeout_sec: POST Request timeout

		"""

		_RECORD_SEND = True
		_RES_ID = False

		# Estos paquetes se envían de forma agrupada y no se controlan
		if self.name not in ('customer_price', 'pricelist_item', 'product_stock'):
			# Check record and get required params
			_RECORD_SEND, _RES_ID, _EXPORT_ID = self.can_send()

		if _RECORD_SEND and self.data:

			jsync_post = None

			# Header
			header_dict = { 'Content-Type': 'application/json' }

			# Content
			json_data = json_dump({
				'object': self.name,
				'operation': self.mode,
				'data': self.data
			})

			# Debug
			debug_msg = "JSync Response: {}" \
						"\n    - object: {}" \
						"\n    - operation: {}" \
						"\n    - data: {}" 

			try:

				# Send HTTP POST data
				jsync_post = self.session.post(self.settings['url'], timeout=timeout_sec, headers=header_dict, data=json_data)

			except Exception as e:

				if self.settings['conexion_error']:
					if type(e) is not ValidationError:
						raise ValidationError("JSync Server Connection Error\n%s" % (e))
					else:
						raise e

			# Si la respuesta es OK
			if jsync_post and jsync_post.status_code is 200:

				_logger.debug(debug_msg.format(jsync_post.text, self.name, self.mode, self.data))

				# En los paquetes múltiples no se establecen estos parámetros
				# por lo que no se notifican al usuario ni se registran en el sistema
				if self.name and self.id and self.model:

					# Mostrar notificación no invasiva al usuario en Odoo
					if notify and 'show_b2b_notifications' in self.env.user and self.env.user.show_b2b_notifications:
						self.env.user.notify_info('[B2B] %s <b>%s</b> %s' % (self.mode.capitalize(), self.name, self.id))

					if _RES_ID:
						# Guardar el estado en Odoo
						with api.Environment.manage():
							with registry.RegistryManager.get(self.env.cr.dbname).cursor() as new_cr:
								new_cr.autocommit(True)
								if not _EXPORT_ID and self.mode == 'create':
									new_cr.execute("INSERT INTO b2b_export (name, rel_id, res_id, create_date) VALUES (%s, %s, %s, %s)", (self.name, self.related, _RES_ID, datetime.now()))
								elif _EXPORT_ID and self.mode == 'update':
									new_cr.execute("UPDATE b2b_export SET name=%s, rel_id=%s, write_date=%s WHERE id=%s", (self.name, self.related, datetime.now(), _EXPORT_ID))
								elif _EXPORT_ID and self.mode == 'delete':
									new_cr.execute("DELETE FROM b2b_export WHERE res_id LIKE %s OR rel_id LIKE %s", (_RES_ID, _RES_ID))

				try:
					return json_load(jsync_post.text)
				except:
					return 'Error de conexión con JSync'

			else:
				_logger.error("JSYNC RESPONSE ERROR: %s" % jsync_post.text)
				_logger.error(debug_msg.format(jsync_post.text, self.name, self.mode, self.data))
				
				if jsync_post and self.settings['conexion_error'] and self.settings['response_error']:
					raise ValidationError("JSync Server Response Error\n%s" % (jsync_post.text.encode('latin1').capitalize()))

		else:
			_logger.warning("El paquete para '%s' no se envió en modo '%s' ya que no cumple las condiciones!" % (self.name, self.mode))

		return False