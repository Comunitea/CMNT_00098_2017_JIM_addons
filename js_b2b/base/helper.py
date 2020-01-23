# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.http import request as HttpRequest
from odoo.exceptions import ValidationError
from unidecode import unidecode
import requests as request
import json

class OutputHelper:

	OK = '\033[92m' # Green
	ERROR = '\033[91m' # Red
	ENDC = '\033[0m' # End
	DIVIDER = "=" * 80 # Divider line

	@staticmethod
	def print_text(msg, msg_type='', include_timestamp=True):
		"""
		Prints a formatted output message

		"""

		print("\n")
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))

		if include_timestamp:
			print("{}{}{}".format(msg_type, datetime.now(), OutputHelper.ENDC))

		print("    {}{}{}".format(msg_type, msg, OutputHelper.ENDC))
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))
		print("\n")

class JSync:

	obj_id = None # Item id
	obj_name = None # Data item name
	obj_dest = 'all' # Client ID or string
	obj_data = {} # Item data dict
	obj_images = [] # Item images list

	def __init__(self, id=None):
		self.obj_id = id

	def filter_obj_data(self, vals=None):
		"""
		Filter and normalizes item data (obj_data)

		:param vals: Item data to update (from model)
		:return: dict

		obj_data key modifiers:
			fixed:xxx -> Sends xxx always
			upload:xxx -> Upload xxx to public server and returns URL
			field_xxx_name:xxx -> Sends xxx field if field_xxx_name has changed
			xxx: -> Sends xxx field if has changed (no modifier)
		"""
		if self.obj_data and type(self.obj_data) is dict:
			for field, value in self.obj_data.items():
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
						self.obj_data[obj_new] = self.obj_data.pop(field)
					if obj_old != 'fixed' and (vals is False or (type(vals) is dict and obj_old not in vals)):
						# Remove field because is not found in vals
						del self.obj_data[obj_new]
					elif type(value) is list:
						# Convert lits to tuples
						self.obj_data[obj_new] = tuple(value)
					elif type(value) is unicode:
						# Decode unicode str's to utf-8
						self.obj_data[obj_new] = value.decode('utf-8', 'replace')
				elif vals is False:
					self.obj_data[field] = None

		return self.obj_data

	def send(self, path='', action='create', timeout_sec=10):
		"""
		Sends data to JSync server and prints on screen

		:param path: URL path to post
		:param action: CRUD action
		:param timeout_sec: POST Request timeout

		"""

		if self.obj_id and self.obj_name:

			# Header
			header_dict = { 
				'Content-Type': 'application/json' 
			}

			# Content
			data_dict = {
				'id': self.obj_id,
				'name': self.obj_name,
				'receivers': self.obj_dest,
				'operation': action,
				'data': self.obj_data,
				'images': self.obj_images
			}

			# Debug
			debug_msg = "JSync Response: {}" \
						"\n    - id: {}" \
						"\n    - name: {}" \
						"\n    - receivers: {}" \
						"\n    - operation: {}" \
						"\n    - data: {}"

			json_data = json.dumps(data_dict)
			debug_data = json.dumps(data_dict.get('data'), indent=8, sort_keys=True)
			b2b_settings = HttpRequest.env['b2b.settings'].get_default_params(fields=['url', 'conexion_error', 'response_error'])

			try:
				
				jsync_res = request.post(b2b_settings['url'] + path, timeout=timeout_sec, headers=header_dict, data=json_data)
				OutputHelper.print_text(debug_msg.format(jsync_res.text, data_dict.get('id'), data_dict.get('name'), data_dict.get('receivers'), data_dict.get('operation'), debug_data), OutputHelper.OK)

				if jsync_res.status_code is not 200 and b2b_settings['conexion_error'] and b2b_settings['response_error']:
					raise ValidationError("JSync Server Response Error\n%s" % (jsync_res.text.encode('latin1').capitalize()))

				try:
					return json.loads(jsync_res.text)
				except:
					return jsync_res.text

			except Exception as e:
				OutputHelper.print_text(debug_msg.format('CONNECTION ERROR!', data_dict.get('id'), data_dict.get('name'), data_dict.get('receivers'), data_dict.get('operation'), debug_data), OutputHelper.ERROR)
				if b2b_settings['conexion_error']:
					if type(e) is not ValidationError:
						raise ValidationError("JSync Server Connection Error\n%s" % (e))
					else:
						raise e