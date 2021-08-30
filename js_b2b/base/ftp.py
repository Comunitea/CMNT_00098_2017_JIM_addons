# -*- coding: utf-8 -*-
from ftplib import FTP_TLS, all_errors
import requests
import logging
import base64
import uuid
import io

# lib to know file extension (only for images)
import imghdr

_logger = logging.getLogger(__name__)
_debug_level = 1 # 1 Low or 2 High

#   _____ _____ _____    _____ _____ __    _____ _____ _____
#  |   __|_   _|  _  |  |  |  |   __|  |  |  _  |   __| __  |
#  |   __| | | |   __|  |     |   __|  |__|   __|   __|    -|
#  |__|    |_| |__|     |__|__|_____|_____|__|  |_____|__|__|
#

def _ftp_connect(settings):
	"""
	FTP TLS Connection from settings
	"""
	try:
		ftps = FTP_TLS(settings.get('server'), settings.get('user'), settings.get('password'))

		# Set debug (if debug mode is ON)
		if request.debug:
			ftps.set_debuglevel(_debug_level)
		# Secure connection
		ftps.prot_p()
		return ftps

	except Exception as e:
		_logger.error('Connection Error: %s', e)
	return False

def _img_extension(bytestream):
	"""
	Get base64 bytestream extension
	:param bytestream: List of bytes
	:return string: File extension
	"""
	return imghdr.what(None, h=bytestream).replace('jpeg', 'jpg')

def _redundant_check(filename):
	"""
	Redundant file check
	:param filename: Image complete name
	:return bool: File exists
	"""
	try:
		base_url = request.env['b2b.settings'].get_param('base_url')
		response = requests.get(base_url + filename, stream=True)
		if response.status_code == 200:
			return True
	except Exception as e:
		_logger.error('Redundant Check Error: %s', e)
	return False

def save_file(filename, settings):
	"""
	Save local file on FTP server
	:param filename: String, file name
	:return bool: File saved
	"""
	if filename:
		try:
			ftps = _ftp_connect(settings)
			if ftps:
				file = open(filename, 'rb')
				ftps.storbinary('STOR ' + filename, file)
				file.close() # Free file memory
				ftps.quit()
				_logger.info('File [%s] saved!', filename)
				return True
		except (all_errors, Exception) as e:
			_logger.error('File Error: %s', e)
	return False

def save_base64(base64_str, settings):
	"""
	Save decoded base64 on FTP server
	:param filename_without_ext: String, file name
	:param base64_str: String, base64 string
	:return str|bool: File name or False
	"""
	bytestream = base64.b64decode(base64_str)
	filename = '%s.%s' % (uuid.uuid4(), _img_extension(bytestream))

	if filename and bytestream:
		try:
			ftps = _ftp_connect(settings)
			if ftps:
				file = io.BytesIO(bytestream)
				ftps.storbinary('STOR ' + filename, file)
				file.close() # Free file memory
				ftps.quit()
				_logger.info('File stream [%s] saved!', filename)
				return filename
		except (all_errors, Exception) as e:
			_logger.error('Bytes Error: %s', e)
	return False

def delete_file(filename, settings):
	"""
	Delete file from FTP server
	:param filename: String, file name
	:return bool: File deleted
	"""
	if filename:
		try:
			ftps = _ftp_connect(settings)
			if ftps:
				ftps.delete(filename)
				ftps.quit()
				_logger.info('File [%s] deleted!', filename)
				return True
		except all_errors as e:
			_logger.error('Delete Error: %s', e)
	return False