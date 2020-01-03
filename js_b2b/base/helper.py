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
	obj_type = False # Data item type (Normal:False|Premium:True)
	obj_data = {} # Item data dict

	def __init__(self, obj_id=None):
		self.obj_id = obj_id

	def filter_obj_data(self, vals=None):
		# Si obj_data es una actualización
		if self.obj_data and type(self.obj_data) is dict:
			# Eliminar campos que no se modificaron
			for field, value in self.obj_data.items():
				# Si el objeto tiene : significa que es un campo relaccionado
				# el string antes de los : es la relacción, a no ser que el string
				# sea 'fixed' en cuyo caso nunca se elimina
				obj_attr = field[:field.index(':')] if ':' in field else field
				# Si se estableció vals es una actualización,
				# quitamos los campos que no cambiaron
				if vals and obj_attr != 'fixed' and obj_attr not in vals:
					del self.obj_data[field]
				elif ':' in field:
					obj_new = field[1+field.index(':'):]
					self.obj_data[obj_new] = self.obj_data.pop(field)
				# Si es un campo Unicode lo pasamos a UTF-8
				elif type(value) is unicode:
					self.obj_data[field] = value.decode('utf-8')
		return self.obj_data

	def send(self, path='', action='create', timeout_sec=10):
		if self.obj_id and self.obj_name:

			header_dict = { 
				'Content-Type': 'application/json' 
			}

			data_dict = {
				'id': self.obj_id,
				'name': self.obj_name,
				'premium': self.obj_type,
				'operation': action,
				'data': self.obj_data
			}

			debug_msg = "JSync Response: {}" \
						"\n    - id: {}" \
						"\n    - name: {}" \
						"\n    - premium: {}" \
						"\n    - operation: {}" \
						"\n    - data: {}"

			b2b_conexion_error = HttpRequest.env['ir.values'].get_default('base.config.settings', 'b2b_conexion_error')
			b2b_response_error = HttpRequest.env['ir.values'].get_default('base.config.settings', 'b2b_response_error')

			try:
				jsync_res = request.post(os.environ['JSYNC_SERVER_URL'] + path, timeout=timeout_sec, headers=header_dict, data=json.dumps(data_dict))
				OutputHelper.print_text(debug_msg.format(jsync_res.text, data_dict.get('id'), data_dict.get('name'), data_dict.get('premium'), data_dict.get('operation'), json.dumps(data_dict.get('data'), indent=8, sort_keys=True)), OutputHelper.OK)

				if jsync_res.status_code is not 200 and b2b_conexion_error and b2b_response_error:
					raise ValidationError("JSync Server Response Error\n%s" % (jsync_res.text))

				try:
					return json.loads(jsync_res.text)
				except:
					return jsync_res.text

			except Exception as e:
				OutputHelper.print_text(debug_msg.format('CONNECTION ERROR!', data_dict.get('id'), data_dict.get('name'), data_dict.get('premium'), data_dict.get('operation'), json.dumps(data_dict.get('data'), indent=8, sort_keys=True)), OutputHelper.ERROR)
				if b2b_conexion_error:
					raise ValidationError("JSync Server Connection Error\n%s" % (e))