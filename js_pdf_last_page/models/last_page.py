# -*- coding: utf-8 -*-
from odoo import api, fields, models

from odoo.exceptions import UserError
from odoo.sql_db import TestCursor
from odoo.tools import config
from functools import partial
import lxml.html

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

class Report(models.Model):
	_inherit = 'report'

	def _get_pdf(self, docids, report_name, html=None, data=None):
		""" 
		Función de bajo nivel para poder sobreescribirla fácilmente
		"""

		if self._check_wkhtmltopdf() == 'install':
			# wkhtmltopdf is not installed
			# the call should be catched before (cf /report/check_wkhtmltopdf) but
			# if get_pdf is called manually (email template), the check could be
			# bypassed
			raise UserError(_("Unable to find Wkhtmltopdf on this system. The PDF can not be created."))

		# As the assets are generated during the same transaction as the rendering of the
		# templates calling them, there is a scenario where the assets are unreachable: when
		# you make a request to read the assets while the transaction creating them is not done.
		# Indeed, when you make an asset request, the controller has to read the `ir.attachment`
		# table.
		# This scenario happens when you want to print a PDF report for the first time, as the
		# assets are not in cache and must be generated. To workaround this issue, we manually
		# commit the writes in the `ir.attachment` table. It is done thanks to a key in the context.
		context = dict(self.env.context)
		if not config['test_enable']:
			context['commit_assetsbundle'] = True

		# Disable the debug mode in the PDF rendering in order to not split the assets bundle
		# into separated files to load. This is done because of an issue in wkhtmltopdf
		# failing to load the CSS/Javascript resources in time.
		# Without this, the header/footer of the reports randomly disapear
		# because the resources files are not loaded in time.
		# https://github.com/wkhtmltopdf/wkhtmltopdf/issues/2083
		context['debug'] = False

		if html is None:
			html = self.with_context(context).get_html(docids, report_name, data=data)

		# The test cursor prevents the use of another environnment while the current
		# transaction is not finished, leading to a deadlock when the report requests
		# an asset bundle during the execution of test scenarios. In this case, return
		# the html version.
		if isinstance(self.env.cr, TestCursor):
			return html

		html = html.decode('utf-8')  # Ensure the current document is utf-8 encoded.

		# Get the ir.actions.report.xml record we are working on.
		report = self._get_report_from_name(report_name)
		# Check if we have to save the report or if we have to get one from the db.
		save_in_attachment = self._check_attachment_use(docids, report)
		# Get the paperformat associated to the report, otherwise fallback on the company one.
		if not report.paperformat_id:
			user = self.env['res.users'].browse(self.env.uid)  # Rebrowse to avoid sudo user from self.env.user
			paperformat = user.company_id.paperformat_id
		else:
			paperformat = report.paperformat_id

		# Preparing the minimal html pages
		page_number = 0
		headerhtml = []
		contenthtml = []
		footerhtml = []
		irconfig_obj = self.env['ir.config_parameter'].sudo()
		base_url = irconfig_obj.get_param('report.url') or irconfig_obj.get_param('web.base.url')

		# Minimal page renderer
		view_obj = self.env['ir.ui.view']
		render_minimal = partial(view_obj.with_context(context).render_template, 'report.minimal_layout')

		# The received html report must be simplified. We convert it in a xml tree
		# in order to extract headers, bodies and footers.
		try:
			root = lxml.html.fromstring(html)
			match_klass = "//div[contains(concat(' ', normalize-space(@class), ' '), ' {} ')]"

			for node in root.xpath(match_klass.format('header')):
				body = lxml.html.tostring(node)
				header = render_minimal(dict(subst=True, body=body, base_url=base_url))
				headerhtml.append(header)

			for node in root.xpath(match_klass.format('footer')):
				body = lxml.html.tostring(node)
				footer = render_minimal(dict(subst=True, body=body, base_url=base_url))
				footerhtml.append(footer)

			for node in root.xpath(match_klass.format('page')):
				# Previously, we marked some reports to be saved in attachment via their ids, so we
				# must set a relation between report ids and report's content. We use the QWeb
				# branding in order to do so: searching after a node having a data-oe-model
				# attribute with the value of the current report model and read its oe-id attribute
				if docids and len(docids) == 1:
					reportid = docids[0]
				else:
					# DON'T SAVE COMPOSED DOCUMENTS
					save_in_attachment = {}
					oemodelnode = node.find(".//*[@data-oe-model='%s']" % report.model)
					if oemodelnode is not None:
						reportid = oemodelnode.get('data-oe-id')
						if reportid:
							reportid = int(reportid)
					else:
						reportid = False

				# Extract the body
				body = lxml.html.tostring(node)
				reportcontent = render_minimal(dict(subst=False, body=body, base_url=base_url))
				contenthtml.append(tuple([reportid, reportcontent]))

				if reportid:
					# Add PDF Last Page
					if not 'user' in locals():
						user = self.env['res.users'].browse(self.env.uid)
					report_record = self.env[report.model].browse(reportid)
					company_id = report_record.company_id if report_record and hasattr(report_record, 'company_id') else user.company_id

					# import pdb; pdb.set_trace()
					for page in company_id.pdf_last_pages.filtered(lambda p: report_name in p.report_ids.mapped('report_name')):
						page_number += 1
						head = '<div style="padding-top: 20px">%s</div>' % page.body
						header = render_minimal(dict(subst=True, body=head, base_url=base_url))
						headerhtml.insert(page_number, header)
						# Si pasamos el ID a False no se crea el adjunto
						# por eso la hay que meter aquí
						contenthtml.insert(page_number, tuple([False, '']))
						footerhtml.insert(page_number, '')
				page_number += 1

		except lxml.etree.XMLSyntaxError:
			contenthtml = []
			contenthtml.append(html)
			save_in_attachment = {}  # Don't save this potentially malformed document

		# Get paperformat arguments set in the root html tag. They are prioritized over
		# paperformat-record arguments.
		specific_paperformat_args = {}
		for attribute in root.items():
			if attribute[0].startswith('data-report-'):
				specific_paperformat_args[attribute[0]] = attribute[1]

		# Return list
		return [
			headerhtml, 
			footerhtml, 
			contenthtml, 
			context.get('landscape'), 
			paperformat, 
			specific_paperformat_args, 
			save_in_attachment, 
			context.get('set_viewport_size')
		]

	@api.model
	def get_pdf(self, docids, report_name, html=None, data=None):
		""" 
		Debido a la mala estructuración del módulo no encontramos como hacer esto sin sobreescribir toda la función 
		antes se había probado con este XML pero generaba 2 adjuntos por documento (uno con el documento y otro con la última página)

		<template id="js_pdf_last_page_content" inherit_id="report.html_container" name="Last Reports Page">
			<xpath expr="." position="inside">
				<!-- Multicompañía -->
				<t t-if="not o and doc" t-set="o" t-value="doc"/>
				<t t-if="o and 'company_id' in o" t-set="company" t-value="o.company_id"/>
				<t t-else="">
					<!-- Por alguna razón aquí llega docs a veces con sólo un documento -->
					<t t-if="docs and (len(docs) == 1 and 'company_id' in docs[0])" t-set="company" t-value="docs[0].company_id"/>
					<t t-else="" t-set="company" t-value="res_company"/>
				</t>

				<!-- Última página -->
				<t t-foreach="company.pdf_last_pages" t-as="last_page">
					<t t-if="xmlid in last_page.report_ids.mapped('report_name')">
						<div class="page js_last_page">
							<!-- Se mete en el header para que no quede un espacio en la parte superior -->
							<div class="header">
								<div style="padding-top: 20px">
									<t t-raw="last_page.body" />
								</div>
							</div>
							<!-- Fake Divs -->
							<div class="invisible">Fake</div>
							<div class="footer"></div>
						</div>
					</t>
				</t>
			</xpath>
		</template>
		"""

		wkhtmltopdf_args = self._get_pdf(docids, report_name, html, data)

		# Run wkhtmltopdf process
		return self._run_wkhtmltopdf(*wkhtmltopdf_args)