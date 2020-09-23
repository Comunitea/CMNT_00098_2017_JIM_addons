# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError
from re import search as validate
import logging

_logger = logging.getLogger('B2B-RES.PARTNER')

# Email PCRE regex validation RFC2822 - https://regexr.com/2rhq7
_email_rfc822_validation = "[a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*@(?:[a-z0-9](?:[a-z0-9-]*[a-z0-9])?\\.)+[a-z0-9](?:[a-z0-9-]*[a-z0-9])?"

class MergePartner(models.TransientModel):
	_inherit = 'base.partner.merge.automatic.wizard'

	@api.multi
	def action_merge(self):
		packets = list()

		# Partners to unlink
		for partner in self.partner_ids - self.dst_partner_id:
			packets += partner.b2b_record('delete', False, auto_send=False)
		
		super(MergePartner, self).action_merge()

		# Send delete packets
		for packet in packets:
			packet.send(notify=False)

		# Check if new partner is notifiable and trigger actions
		if self.dst_partner_id.is_notifiable_check():
			self.dst_partner_id.b2b_record('create')
		else:
			self.dst_partner_id.b2b_record('delete')

class ResPartner(models.Model):
	_inherit = 'res.partner'

	vip_web_access = fields.Many2many('res.company', 'res_partner_res_company_web_access', string='VIP Webs Access')

	@api.multi
	def __check_vip_web_access_companies_pricelists(self, vals=dict()):
		if vals.get('vip_web_access', False):
			# Comprobar tarifa por compañía web
			# se usa una consulta porque la operación es más rápida que por el ORM
			for record in self:
				self.env.cr.execute("SELECT company_id FROM ir_property WHERE name LIKE 'property_product_pricelist' and res_id = 'res.partner,%s'", (record.id,))
				pricelists_company_ids = [r[0] for r in self.env.cr.fetchall()]
				for company in record.vip_web_access:
					if company.id not in pricelists_company_ids:
						raise ValidationError(_('Unable to set web access for %s\nClient don\'t have pricelist on this company!') % company.name)

	@api.multi
	def has_valid_emails(self):
		self.ensure_one()
		
		# Test email/s
		email_valid = validate(_email_rfc822_validation, self.email) if self.email else None

		# Si el/los emails son válidos
		if self.email and email_valid:
			return True

		return False

	@api.multi
	def primary_email(self):
		self.ensure_one()

		# Test email/s
		email_valid = validate(_email_rfc822_validation, self.email) if self.email else None

		# Si el/los emails son válidos
		if self.email and email_valid:
			# Devolver el primer email
			return email_valid.group()

		return False

	@api.constrains('email')
	def _check_email_address(self):
		for record in self:
			if record.email and not record.has_valid_emails():
				raise ValidationError(_('Partner email is not valid, check it!'))

	@api.constrains('vip_web_access')
	def __check_vip_web_access_companies_pricelists(self):
		# Comprobar tarifa por compañía web
		# se usa una consulta porque la operación es más rápida que por el ORM
		for record in self:
			if record.vip_web_access:
				self.env.cr.execute("SELECT company_id FROM ir_property WHERE name LIKE 'property_product_pricelist' and res_id = 'res.partner,%s'", (record.id,))
				pricelists_company_ids = [r[0] for r in self.env.cr.fetchall()]
				for company in record.vip_web_access:
					if company.id not in pricelists_company_ids:
						raise ValidationError(_('Unable to set web access for %s\nClient don\'t have pricelist on this company!') % company.name)
