# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import xml.etree.ElementTree as xee
from ...js_b2b.base.helper import JSync
from .. import constants

PARAM_TEMPLATE_FIELD = 'parameterization_template'
PRODUCT_PARAMETERIZATION = 'product.parameterization'
PARAM_FIELDS_XPATH = './/div[@id="parameterization_fields"]'
PRODUCT_PARAM_FORM_ID = 'js_parameterization.parameterization_product_form_view'

class ParameterizationField(models.TransientModel):
	_name = 'js_parameterization.field'

	@api.multi
	def set_domain(self):
		view_id = self.env.ref(PRODUCT_PARAM_FORM_ID)
		model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.parameterization')])
		field_list = [tag.attrib['name'] for tag in xee.fromstring(str(view_id.arch_base)).findall('%s//field' % PARAM_FIELDS_XPATH)]
		return [('model_id', '=', model_id.id), ('state', '=', 'base'), ('name', 'in', field_list)]

	parameterization_fields = fields.Many2many('ir.model.fields', 'ir_model_field_js_field_wizard_rel', 'field_wizard_id', 'ir_model_field_id', domain=set_domain, required=True)
	action = fields.Selection([('CREATE', 'CREATE'), ('UPDATE', 'UPDATE'), ('DELETE', 'DELETE')], required=True, default='CREATE')

	#@api.model
	#def __remove_field(self, field_name):
	#	self.env.cr.execute("""
	#		DELETE FROM ir_model_fields WHERE model = 'product.parameterization' AND name=%s; 
	#		ALTER TABLE product_parameterization DROP COLUMN %s;
	#	""", (field_name, field_name)).commit()

	@api.model
	def __parameterization_fields(self):
		fields_dict = dict()
		view_id = self.env.ref(PRODUCT_PARAM_FORM_ID)

		for group in xee.fromstring(str(view_id.arch_base)).findall('%s//group//group' % PARAM_FIELDS_XPATH):
			group_attrs = safe_eval(group.attrib.get('attrs', '{}'))
			groups_attr_invisible = group_attrs.get('invisible')
			group_fields = tuple([field.attrib.get('name') for field in group.findall('.//field')])
			if groups_attr_invisible and group_fields:
				for domain_item in groups_attr_invisible:
					is_valid_domain = type(domain_item) in (list, tuple) and len(domain_item)==3
					is_param_domain = (is_valid_domain and domain_item[0] == PARAM_TEMPLATE_FIELD and domain_item[1] == '!=')
					if is_param_domain: fields_dict.update({ int(domain_item[2]): group_fields })
			elif not groups_attr_invisible:
				fields_dict.update({ 0: group_fields })

		return fields_dict.items()

	@api.model
	def __template_translations(self, template_id):
		templates_dict = dict(constants.TEMPLATES_LIST)
		template_name = templates_dict.get(template_id, str())
		field_name = '%s,%s' % (PRODUCT_PARAMETERIZATION, PARAM_TEMPLATE_FIELD)
		self._cr.execute("""
			SELECT 'en-US' AS lang, %s AS value 
			UNION 
			SELECT replace(lang, '_', '-') as lang, value 
			FROM public.ir_translation 
			WHERE name LIKE %s 
			AND type LIKE 'selection' 
			AND src LIKE %s 
			GROUP BY lang, value""", (template_name, field_name, template_name))
		return dict(self._cr.fetchall())

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
		selected_fields_list = self.parameterization_fields.mapped('name')
		for group, fields in self.__parameterization_fields():
			for field_name in fields:
				if field_name in selected_fields_list:
					field = self.parameterization_fields.filtered(lambda r: r.name == field_name)
					field.ensure_one()

					group_names = self.__template_translations(group)
					field_names = field.get_field_translations('field_description')
					merged_names = { k: '[%s] %s' % (group_names[k], field_names[k]) for k in field_names.keys() if k in group_names }

					packet = JSync(self.env)
					packet.id = field.id
					packet.model = 'ir.model_fields'
					packet.name = 'parameterization_field'
					packet.mode = self.action.lower()
					packet.data = { 
						'jim_id': field.id, 
						'name': merged_names
					}

					if packet.send() and self.action == 'DELETE':
						for value in self.env['js_parameterization.value'].search([('fields', 'in', field.id)]):
							value.fields = [(3, field.id)]