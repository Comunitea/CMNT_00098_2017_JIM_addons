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
import threading
import logging

_logger = logging.getLogger('B2B-OUTGOING')
_thread_semaphore = threading.BoundedSemaphore(20)

class Thread(threading.Thread):

	def run(self):
		_thread_semaphore.acquire()
		try:
			self.background_run(*self._Thread__args)
		finally:
			_thread_semaphore.release()

	def background_run(self, method, record, mode):
		"""
		Method to be called in a separate thread

		:param method: Object, method to call
		:param record: Object, record to notify
		:param mode: Str, CRUD mode
		"""
		while not self._Thread__target.env.cr.closed:
			# Wait while parent process ends
			sleep(5)

		# Now create a new cursor
		with api.Environment.manage():
			with self._Thread__target.pool.cursor() as new_cr:
				# Autocommit ON
				new_cr.autocommit(True)
				# Issolated record
				record_issolated = record.with_env(record.env(cr=new_cr))
				# Call the method
				method(record_issolated, mode)

class Chrono(object):

	__slots__ = ['name', 'start', 'end', 'elapsed']

	def __init__(self, name=None):
		self.name = name
		self.start = None
		self.end = None
		self.elapsed = None

	def __enter__(self):
		self.start = default_timer()
		return self

	def __exit__(self,ty,val,tb):
		self.end = default_timer()
		self.elapsed = self.end - self.start

	def to_str(self):
		if self.elapsed:
			return "%.2fms" % (self.elapsed)
		return None

class JSync(object):

	__slots__ = ['id', 'env', 'model', 'mode', 'name', 'data', 'part', 'related', 'session', 'settings']

	def __init__(self, odoo_env, settings=None, retries=3):
		retry = httpRetry(total=retries, connect=retries, backoff_factor=0.3, status_forcelist=(500, 502, 504))
		adapter = HTTPAdapter(max_retries=retry)

		self.id = None # Record ID
		self.model = None # Record model name
		self.mode = 'create' # CRUD mode
		self.name = None # Data item name
		self.data = {} # Item data dict
		self.part = None # Multi-packet part
		self.related = None # Odoo related model & record
		self.env = odoo_env # Odoo environment
		self.session = Session() # HTTP Session
		self.session.mount('http://', adapter)
		self.session.mount('https://', adapter)

		# If settings passed use it to avoid multiple calls
		self.settings = settings or self.env['b2b.settings'].get_default_params(fields=[
			'url', 
			'conexion_error', 
			'response_error', 
			'packet_size'
		])

	def filter_data(self, vals=None):
		"""
		Filter and normalizes item data (data)

		:param vals: Item data to update (from model)
		:return: dict

		data key modifiers:
			fixed:xxx -> Sends xxx always
			field_xxx_name:xxx -> Sends xxx field if field_xxx_name has changed
			xxx: -> Sends xxx field if has changed (no modifier)
		"""
		if self.data and type(self.data) is dict:
			for field, value in self.data.items():
				obj_old = obj_new = field
				# If field have :
				if ':' in field:
					# Before :
					obj_old = field[:field.index(':')]
					# After :
					obj_new = field[field.index(':') + 1:]
					# Replace key
					self.data[obj_new] = self.data.pop(field)
				if obj_old != 'fixed' and (vals is False or (type(vals) is dict and obj_old not in vals)):
					# Remove field because is not found in vals
					del self.data[obj_new]
				elif type(value) is list:
					# Convert lits to tuples
					self.data[obj_new] = tuple(value)
				elif type(value) is unicode:
					# Decode unicode str's to utf-8
					self.data[obj_new] = value.strip().decode('utf-8', 'replace')

		return self.data

	def send(self, timeout_sec=10, notify=True, **kwargs):
		"""
		Sends data to JSync server and prints on screen

		:param action: CRUD action
		:param timeout_sec: POST Request timeout

		"""

		# Odoo resource name
		res_id = '%s,%s' % (self.model, self.id)

		# Check if record is synced with JSync
		export_record = self.env['b2b.export'].search([('res_id', '=', res_id)], limit=1)

		# Send the record?
		record_send = (not export_record or self.mode != 'create')

		if self.name and self.data and self.mode and record_send:

			jsync_post = None

			# Header
			header_dict = { 'Content-Type': 'application/json' }

			# Content
			json_data = json_dump({
				'object': self.name,
				'operation': self.mode,
				'data': self.data,
				'part': self.part
			})

			# Debug
			debug_msg = "JSync Response: {}" \
						"\n    - object: {}" \
						"\n    - operation: {}" \
						"\n    - data: {}" \
						"\n    - part: {}"

			# Data indented (pretified)
			debug_data = json_dump(self.data, indent=8, sort_keys=True)

			try:
				
				# Send HTTP POST data
				jsync_post = self.session.post(self.settings['url'], timeout=timeout_sec, headers=header_dict, data=json_data)
					
			except Exception as e:

				_logger.error(debug_msg.format('CONNECTION ERROR!', self.name, self.mode, debug_data, self.part))
				
				if self.settings['conexion_error']:
					if type(e) is not ValidationError:
						raise ValidationError("JSync Server Connection Error\n%s" % (e))
					else:
						raise e

			# Si la respuesta es OK
			if jsync_post and jsync_post.status_code is 200:

				_logger.info(debug_msg.format(jsync_post.text, self.name, self.mode, debug_data, self.part))

				# En los paquetes múltiples no se establecen estos parámetros
				# por lo que no se notifican al usuario ni se registran en el sistema
				if self.name and self.id and self.model:

					# Mostrar notificación no invasiva al usuario en Odoo
					if notify:
						self.env.user.notify_info('[B2B] %s <b>%s</b> %s' % (self.mode.capitalize(), self.name, self.id))

					# Guardar el estado en Odoo
					if self.mode == 'create':
						self.env['b2b.export'].create({ 'name': self.name, 'res_id': res_id, 'rel_id': self.related })
					elif self.mode == 'update':
						export_record.write({ 'name': self.name, 'res_id': res_id, 'rel_id': self.related })
					elif self.mode == 'delete':
						export_record.unlink()

				try:
					return json_load(jsync_post.text)
				except:
					return jsync_post.text

			elif jsync_post:

				_logger.error(debug_msg.format('RESPONSE ERROR!', self.name, self.mode, debug_data, self.part))
				
				if self.settings['conexion_error'] and self.settings['response_error']:
					raise ValidationError("JSync Server Response Error\n%s" % (jsync_post.text.encode('latin1').capitalize()))

		return False