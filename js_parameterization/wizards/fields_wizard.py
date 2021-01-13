# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import xml.etree.ElementTree as xee
from ...js_b2b.base.helper import JSync

class ParameterizationField(models.TransientModel):
	_name = 'js_parameterization.field'

	@api.multi
	def set_domain(self):
		view_id = self.env.ref('js_parameterization.parameterization_product_form_view')
		model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.parameterization')])
		field_list = [tag.attrib['name'] for tag in xee.fromstring(str(view_id.arch_base)).findall('.//div[@id="parameterization_fields"]//field')]
		return [('model_id', '=', model_id.id), ('state', '=', 'base'), ('name', 'in', field_list)]

	# Campos de la parametrización
	# OJO! para poder poner en el atributo domain el resultado de set_domain
	# la función debe estar creada antes
	parameterization_fields = fields.Many2many('ir.model.fields', 'ir_model_field_js_field_wizard_rel', 'field_wizard_id', 'ir_model_field_id', domain=set_domain, required=True)

	# Plantillas de la parametrización
	# En principio no son necesarias en JSYNC
	# parameterization_template = fields.Selection(templates_values.parameterization_template_list, required=False) 

	# Selector de acciones
	action = fields.Selection([
		('CREATE', 'CREATE'),
		('UPDATE', 'UPDATE'),
		('DELETE', 'DELETE')
	], required=True, default='CREATE')

	#@api.model
	#def __remove_field(self, field_name):
	#	self.env.cr.execute("""
	#		DELETE FROM ir_model_fields WHERE model = 'product.parameterization' AND name=%s; 
	#		ALTER TABLE product_parameterization DROP COLUMN %s;
	#	""", (field_name, field_name)).commit()

	@api.onchange('action')
	def __onchange_action(self):
		if self.action == 'DELETE':
			return { 
				'warning' : { 
					'title' : _("Warning"), 'message': _('All parameterization values relations will be deleted!')
				}
			} 

	@api.multi
	def send(self):
		for field in self.parameterization_fields:
			packet = JSync(self.env)
			packet.id = field.id
			packet.model = 'ir.model_fields'
			packet.name = 'parameterization_field'
			packet.mode = self.action.lower()

			packet.data = { 
				'jim_id': field.id, 
				'name': field.get_field_translations('field_description') 
			}

			if packet.send() and self.action == 'DELETE':
				for value in self.env['js_parameterization.value'].search([('fields', 'in', field.id)]):
					value.fields = (3, field.id)