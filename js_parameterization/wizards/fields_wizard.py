# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.tools.safe_eval import safe_eval
import xml.etree.ElementTree as xee
from ...js_b2b.base.helper import JSync
from .. import constants

class ParameterizationField(models.TransientModel):
	_name = constants.PARAMETERIZATION_FIELDS

	@api.multi
	def set_domain(self):
		view_id = self.env.ref(constants.PRODUCT_PARAM_FORM_ID)
		model_id = self.env['ir.model'].sudo().search([('model', '=', constants.PRODUCT_PARAMETERIZATION)])
		field_list = [tag.attrib['name'] for tag in xee.fromstring(str(view_id.arch_base)).findall('%s//field' % constants.PARAM_FIELDS_XPATH)]
		return [('model_id', '=', model_id.id), ('state', '=', 'base'), ('name', 'in', field_list)]

	parameterization_fields = fields.Many2many('ir.model.fields', 'ir_model_field_js_field_wizard_rel', 'field_wizard_id', 'ir_model_field_id', domain=set_domain, required=True)
	action = fields.Selection([('CREATE', 'CREATE'), ('UPDATE', 'UPDATE'), ('DELETE', 'DELETE')], required=True, default='CREATE')

	@api.model
	def parameterization_fields_get(self):
		fields_dict = dict()
		view_id = self.env.ref(constants.PRODUCT_PARAM_FORM_ID)

		for group in xee.fromstring(str(view_id.arch_base)).findall('%s//group//group' % constants.PARAM_FIELDS_XPATH):
			group_attrs = safe_eval(group.attrib.get('attrs', '{}'))
			groups_attr_invisible = group_attrs.get('invisible')
			group_fields = tuple([field.attrib.get('name') for field in group.findall('.//field')])
			if groups_attr_invisible and group_fields:
				for domain_item in groups_attr_invisible:
					is_valid_domain = type(domain_item) in (list, tuple) and len(domain_item)==3
					is_param_domain = (is_valid_domain and domain_item[0] == constants.PARAM_TEMPLATE_FIELD and domain_item[1] == '!=')
					if is_param_domain: fields_dict.update({ int(domain_item[2]): group_fields })
			elif not groups_attr_invisible:
				fields_dict.update({ 0: group_fields })

		return fields_dict.items()

	@api.model
	def __template_translations(self, template_id):
		templates_dict = dict(constants.TEMPLATES_LIST)
		template_name = templates_dict.get(template_id, str())
		field_name = '%s,%s' % (constants.PRODUCT_PARAMETERIZATION, constants.PARAM_TEMPLATE_FIELD)
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

	@api.model
	def _send(self, action, id, name=None):
		packet = JSync(self.env)
		packet.id = id
		packet.model = 'ir.model_fields'
		packet.name = 'parameterization_field'
		packet.mode = self.action.lower()
		packet.data = { 
			'jim_id': id, 
			'name': name
		}

		if packet.send() and self.action == 'DELETE':
			for value in self.env[constants.PARAMETERIZATION_VALUES].search([('fields', 'in', id)]):
				value.fields = [(3, id)]

	@api.multi
	def send(self):
		selected_fields_list = self.parameterization_fields.mapped('name')
		for group, fields in self.parameterization_fields_get():
			for field_name in fields:
				if field_name in selected_fields_list:
					field = self.parameterization_fields.filtered(lambda r: r.name == field_name)
					field.ensure_one()

					group_names = self.__template_translations(group)
					field_names = field.get_field_translations('field_description')
					merged_names = { k: '[%s] %s' % (group_names.get(k, 'Generic'), field_names[k]) if group else field_names[k] for k in field_names.keys() }
					self._send(self.action, field.id, merged_names)