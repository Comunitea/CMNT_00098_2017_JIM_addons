# -*- coding: utf-8 -*-
from datetime import datetime
from requests.adapters import HTTPAdapter
from odoo.http import request as HttpRequest
from requests.packages.urllib3.util.retry import Retry as httpRetry
from odoo.exceptions import ValidationError
from google.cloud import pubsub_v1
from unidecode import unidecode
import requests
import json
import os

#cr = openerp.registry(self.env.cr.dbname).cursor()
#api.Environment(cr, odoo.SUPERUSER_ID, self.env.context)
#api.Environment(self.cr, self.uid, {})

class OutputHelper:

	OK = '\033[92m' # Green
	ERROR = '\033[91m' # Red
	INFO = '\033[38;5;039m' # Blue
	ENDC = '\033[0m' # End
	DIVIDER = "=" * 80 # Divider line

	@staticmethod
	def print_text(msg, msg_type=''):
		"""
		Prints a formatted output message

		"""
		print("\n")
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))
		print("    {}{}{}".format(msg_type, msg, OutputHelper.ENDC))
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))
		print("\n")

class JSync:

	id = None # Item id
	name = None # Data item name
	data = {} # Item data dict
	session = None # HTTP Session

	def __init__(self, id=None, retries=3):
		self.id = id
		self.session = requests.Session()
		retry = httpRetry(total=retries, connect=retries, backoff_factor=0.3, status_forcelist=(500, 502, 504))
		adapter = HTTPAdapter(max_retries=retry)
		self.session.mount('http://', adapter)
		self.session.mount('https://', adapter)

	def filter_data(self, vals=None, delete=False):
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
					if delete or obj_old != 'fixed' and (vals is False or (type(vals) is dict and obj_old not in vals)):
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

	def send(self, path='', action=None, timeout_sec=10):
		"""
		Sends data to JSync server and prints on screen

		:param path: URL path to post
		:param action: CRUD action
		:param timeout_sec: POST Request timeout

		"""

		if self.name and action:

			# Header
			header_dict = { 
				'Content-Type': 'application/json' 
			}

			# Content
			data_dict = {
				'id': self.id,
				'name': self.name,
				'operation': action,
				'data': self.data
			}

			# Debug
			debug_msg = "JSync Response: {}" \
						"\n    - id: {}" \
						"\n    - name: {}" \
						"\n    - operation: {}" \
						"\n    - data: {}"

			json_data = json.dumps(data_dict)
			debug_data = json.dumps(data_dict.get('data'), indent=8, sort_keys=True)
			b2b_settings = HttpRequest.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error'])

			try:
				
				jsync_res = self.session.post(b2b_settings['url'] + path, timeout=timeout_sec, headers=header_dict, data=json_data)
				OutputHelper.print_text(debug_msg.format(jsync_res.text, data_dict.get('id'), data_dict.get('name'), data_dict.get('operation'), debug_data), OutputHelper.OK)

				if jsync_res.status_code is not 200 and b2b_settings['conexion_error'] and b2b_settings['response_error']:
					raise ValidationError("JSync Server Response Error\n%s" % (jsync_res.text.encode('latin1').capitalize()))

				try:
					return json.loads(jsync_res.text)
				except:
					return jsync_res.text

			except Exception as e:
				OutputHelper.print_text(debug_msg.format('CONNECTION ERROR!', data_dict.get('id'), data_dict.get('name'), data_dict.get('operation'), debug_data), OutputHelper.ERROR)
				if b2b_settings['conexion_error']:
					if type(e) is not ValidationError:
						raise ValidationError("JSync Server Connection Error\n%s" % (e))
					else:
						raise e

class Google:

	subscriber = None # Google Sub

	def __init__(self):
		self.subscriber = pubsub_v1.SubscriberClient()

	def receive(self, subscription, callback_obj):
		if self.subscriber:
			sub_path = self.subscriber.subscription_path(os.environ['GOOGLE_CLOUD_PROJECT_ID'], subscription)
			flow_control_obj = pubsub_v1.types.FlowControl(max_messages=10)
			return self.subscriber.subscribe(sub_path, callback=callback_obj, flow_control=flow_control_obj)