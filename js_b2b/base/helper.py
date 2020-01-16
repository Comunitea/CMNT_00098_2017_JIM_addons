# -*- coding: utf-8 -*-
from datetime import datetime
from odoo.http import request as HttpRequest
from odoo.exceptions import ValidationError
from unidecode import unidecode
import requests as request
import json
import os

class OutputHelper:

	OK = '\033[92m'
	ERROR = '\033[91m'
	ENDC = '\033[0m'
	DIVIDER = "=" * 80

	@staticmethod
	def print_text(msg, msg_type='', include_timestamp=True):
		print("\n")
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))

		if include_timestamp:
			print("{}{}{}".format(msg_type, datetime.now(), OutputHelper.ENDC))

		print("    {}{}{}".format(msg_type, msg, OutputHelper.ENDC))
		print("{}{}{}".format(msg_type, OutputHelper.DIVIDER, OutputHelper.ENDC))
		print("\n")

	@staticmethod
	def format_date(date_string=None, input_date_format='%Y-%m-%d %H:%M:%S', output_date_format='%Y%m%d'):
		if not date_string:
			date_string = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
		return datetime.strptime(date_string, input_date_format).strftime(output_date_format)

class JSync:

	obj_id = None # Item id
	obj_name = None # Data item name
	obj_dest = 'all' # Client ID or string
	obj_data = {} # Item data dict

	def __init__(self, obj_id=None):
		self.obj_id = obj_id

	def filter_obj_data(self, vals=None):
		# Si obj_data es un diccionario
		if self.obj_data and type(self.obj_data) is dict:
			# Eliminar campos que no se modificaron
			for field, value in self.obj_data.items():
				obj_old = obj_new = field
				# Si el objeto tiene : significa que es un campo relaccionado
				# el string antes de los : es la relacción, a no ser que el string
				# sea 'fixed' en cuyo caso nunca se elimina
				if ':' in field:
					obj_old = field[:field.index(':')]
					obj_new = field[1+field.index(':'):]
					self.obj_data[obj_new] = self.obj_data.pop(field)
				if obj_old != 'fixed' and (type(vals) is dict and obj_old not in vals or vals is False):
					del self.obj_data[obj_new]
				elif type(value) is unicode:
					self.obj_data[obj_new] = value.decode('utf-8')
		return self.obj_data

	def send(self, path='', action='create', timeout_sec=10):
		if self.obj_id and self.obj_name:

			header_dict = { 
				'Content-Type': 'application/json' 
			}

			data_dict = {
				'id': self.obj_id,
				'name': self.obj_name,
				'receivers': self.obj_dest,
				'operation': action,
				'data': self.obj_data
			}

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