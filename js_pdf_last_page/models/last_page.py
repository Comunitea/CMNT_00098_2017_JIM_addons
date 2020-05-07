# -*- coding: utf-8 -*-
from odoo import api, fields, models

class LastReportsPage(models.Model):
	_name = 'reports.last_page'
	_description = 'Documents Last Page'

	body = fields.Html('Body', required=True, translate=True, help="Set last page body")
	company_id = fields.Many2one('res.company', string='Company', required=True, help="Select company to apply")
	report_ids = fields.Many2many('ir.actions.report.xml', string='Associated reports', required=True, help="Select reports")

	@api.onchange('company_id')
	def _onchange_company_id(self):
		# Por defecto no mostramos ninguno hasta seleccionar la empresa
		domain = { 'report_ids': [('id', '=', False)] }

		if self.company_id:
			# IDs usados
			reports_ids = list()
			for last_page in self.search([('company_id', '=', self.env.context.get('default_company_id', self.company_id.id))]):
				reports_ids = reports_ids + last_page.report_ids.ids
			domain = { 'report_ids': [('id', 'not in', reports_ids)] }

		return { 'domain': domain }