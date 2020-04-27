# -*- coding: utf-8 -*-
from datetime import datetime
from requests import Session
from requests.adapters import HTTPAdapter
from odoo.http import request as HttpRequest
from requests.packages.urllib3.util.retry import Retry as httpRetry
from json import loads as json_load, dumps as json_dump
from odoo.exceptions import ValidationError
from google.cloud import pubsub_v1
from unidecode import unidecode
from sys import getsizeof
from os import environ
from math import ceil

class OutputHelper:

	OK = '\033[92m' # Green
	ERROR = '\033[91m' # Red
	INFO = '\033[38;5;039m' # Blue
	ENDC = '\033[0m' # End
	DIVIDER = "=" * 80 # Divider line

	@staticmethod
	def log(msg, msg_type=''):
		print("{}{}{}".format(msg_type, msg, OutputHelper.ENDC if msg_type else ''))

	@staticmethod
	def print_message(msg, msg_type=''):
		"""
		Prints a formatted output message

		"""
		print("\n")
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))
		print("    {}{}{}".format(msg_type, msg, OutputHelper.ENDC))
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))
		print("\n")

class JSync:

	mode = 'create'
	name = None # Data item name
	data = {} # Item data dict
	session = None # HTTP Session
	settings = dict() # JSync Settings
	path = '' # URL Path

	def __init__(self, retries=3, settings=dict()):
		retry = httpRetry(total=retries, connect=retries, backoff_factor=0.3, status_forcelist=(500, 502, 504))
		adapter = HTTPAdapter(max_retries=retry)
		self.session = Session()
		self.session.mount('http://', adapter)
		self.session.mount('https://', adapter)
		self.settings = settings or HttpRequest.env['b2b.settings'].get_default_params()

	def __data_iterator(self):
		"""
		Splits data list in multiple parts

		:param parts: Number of parts
		:return: list of iterators
		"""
		out_it = []
		last = 0.0

		if not self.data or type(self.data) not in (list, tuple):
			return False

		packet_size_mb = self.settings.get('packet_size', 10)
		data_size = getsizeof(self.data)/1048576
		num_packets_total = ceil(data_size / packet_size_mb) or 1
		data_items_count = len(self.data)
		avg = data_items_count / float(num_packets_total)
		while last < data_items_count:
			out_it.append(iter(self.data[int(last):int(last + avg)]))
			last += avg
		return out_it

	def filter_data(self, vals=None):
		"""
		Filter and normalizes item data (data)

		:param vals: Item data to update (from model)
		:return: dict

		data key modifiers:
			fixed:xxx -> Sends xxx always
			upload:xxx -> Upload xxx to public server and returns URL
			field_xxx_name:xxx -> Sends xxx field if field_xxx_name has changed
			xxx: -> Sends xxx field if has changed (no modifier)
		"""
		if self.data and type(self.data) is dict:
			for field, value in self.data.items():
				# Uploads are handled different
				if not field.startswith('upload:'):
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
				# Updating other fields, delete upload
				elif type(vals) is dict and field[7:] not in vals:
					del self.data[field]
				# If we are deleting an image set to NULL
				elif vals is False:
					self.data[field] = None

		return self.data

	def __send(self, data_dict, timeout_sec=10, settings=None):
		"""
		Sends data to JSync server and prints on screen (low private method)

		:param data_dict: valid data dict
		:param action: valid action str

		"""

		# Header
		header_dict = { 'Content-Type': 'application/json' }

		# Debug
		debug_msg = "JSync Response: {}" \
					"\n    - name: {}" \
					"\n    - operation: {}" \
					"\n    - data: {}" \
					"\n    - part: {}"

		json_data = json_dump(data_dict)
		debug_data = json_dump(data_dict.get('data'), indent=8, sort_keys=True)

		try:
			
			endpoint = self.settings.get('url') + self.path
			jsync_res = self.session.post(endpoint, timeout=timeout_sec, headers=header_dict, data=json_data)
			OutputHelper.print_message(debug_msg.format(jsync_res.text, data_dict.get('name'), data_dict.get('operation'), debug_data, data_dict.get('part')), OutputHelper.OK)
			if jsync_res.status_code is not 200 and self.settings['conexion_error'] and self.settings['response_error']:
				raise ValidationError("JSync Server Response Error\n%s" % (jsync_res.text.encode('latin1').capitalize()))
			try:
				return json_load(jsync_res.text)
			except:
				return jsync_res.text

		except Exception as e:
			OutputHelper.print_message(debug_msg.format('CONNECTION ERROR!', data_dict.get('name'), data_dict.get('operation'), debug_data, data_dict.get('part')), OutputHelper.ERROR)
			if self.settings['conexion_error']:
				if type(e) is not ValidationError:
					raise ValidationError("JSync Server Connection Error\n%s" % (e))
				else:
					raise e

	def send(self, **kwargs):
		"""
		Sends data to JSync server and prints on screen

		:param action: CRUD action
		:param timeout_sec: POST Request timeout

		"""
		if self.name and self.data and self.mode:
			# Get multiple data iterators
			# large data sets have to be divided in multiple parts
			# determined by packet_size on settings
			data_list_multiple = self.__data_iterator()

			if data_list_multiple:
				# Multiple
				num_packets = len(data_list_multiple)
				for i in range(num_packets):
					self.__send({
							'name': self.name,
							'operation': self.mode,
							'data': list(data_list_multiple[i]),
							'part': [i + 1, num_packets]
						}, **kwargs)
			else:
				# One
				self.__send({
						'name': self.name,
						'operation': self.mode,
						'data': self.data
					}, **kwargs)
		return True

class Google:

	subscriber = None # Google Sub

	def __init__(self):
		self.subscriber = pubsub_v1.SubscriberClient()

	def receive(self, subscription, callback_obj):
		if self.subscriber:
			sub_path = self.subscriber.subscription_path(environ['GOOGLE_CLOUD_PROJECT_ID'], subscription)
			flow_control_obj = pubsub_v1.types.FlowControl(max_messages=10)
			return self.subscriber.subscribe(sub_path, callback=callback_obj, flow_control=flow_control_obj)