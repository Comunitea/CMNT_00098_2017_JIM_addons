# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from psycopg2.extensions import AsIs
import xml.etree.ElementTree as xee
from .. import constants

PARAM_TEMPLATE_FIELD = 'parameterization_template'
PARAM_FIELDS_XPATH = './/div[@id="parameterization_fields"]'
PRODUCT_PARAM_FORM_ID = 'js_parameterization.parameterization_product_form_view'

class ParameterizationValue(models.Model):
	_name = 'js_parameterization.value'
	_description = "Parameterization Values"
	_order = 'name, fields'

	def set_domain(self):
		view_id = self.env.ref(PRODUCT_PARAM_FORM_ID)
		model_id = self.env['ir.model'].sudo().search([('model', '=', 'product.parameterization')])
		field_list = [tag.attrib.get('name') for tag in xee.fromstring(str(view_id.arch_base)).findall('%s//field' % PARAM_FIELDS_XPATH)]
		return [('model_id', '=', model_id.id), ('state', '=', 'base'), ('name', 'in', field_list)]

	name = fields.Char(required=True, translate=True)
	fields = fields.Many2many('ir.model.fields', 'ir_model_field_js_parameterization_value_rel', 'js_parameterization_value_id', 'ir_model_field_id', domain=set_domain)

	@api.model
	def update_parameterization_relations(self, value_id, field_name):
		parameterization_obj = self.env['product.parameterization'].with_context(b2b_evaluate=False)
		return parameterization_obj.search([(field_name, '=', value_id)]).write({ field_name: False })

	#override
	@api.multi
	def write(self, values):	
		old_fields = self.fields.ids
		super(ParameterizationValue, self).write(values)
		removed_fields = list(set(old_fields) - set(self.fields.ids))

		for field in self.env['ir.model.fields'].browse(removed_fields):
			self.update_parameterization_relations(self.id, field.name)

		return True

class ProductParameterization(models.Model):
	_name = 'product.parameterization'
	_description = "Product Parameterization"
	# [LOIS] Restricción de SQL. En este caso que no existan varias entradas con el mismo id de producto
	_sql_constraints = [('parameterization_product_unique', 'unique(product_tmpl_id)', 'Product must be unique in parameterization!')]
	# [LOIS] Se muestra en las migas de pan, pintaría el id del producto
	_rec_name = 'product_tmpl_id' 

	product_tmpl_id = fields.Many2one('product.template', string='Related Product', required=True, ondelete='cascade')

	# [LOIS] Estado de la parametrización de este producto
	# [LOIS] Si se archiva el producto, la parametrización también, y viceversa
	active = fields.Boolean('Active', related='product_tmpl_id.active', store=False)
	# [LOIS] Crea el select, no carga las opciones de ningún sitio
	# PARAM_TEMPLATE_FIELD Definition
	parameterization_template = fields.Selection(constants.TEMPLATES_LIST, required=False)

	# TODO
	certificaciones_ensayos = fields.Many2one('js_parameterization.value', string='CERTIFICATIONS/TESTS', domain="[('fields.name', '=', 'certificaciones_ensayos')]")
	envase = fields.Many2one('js_parameterization.value', string='PACKAGING', domain="[('fields.name', '=', 'envase')]")
	nivel_habilidad = fields.Many2one('js_parameterization.value', string='SKILL LEVEL', domain="[('fields.name', '=', 'nivel_habilidad')]")
	coleccion = fields.Many2one('js_parameterization.value', string='COLLECTION', domain="[('fields.name', '=', 'coleccion')]")
	reglamentacion = fields.Many2one('js_parameterization.value', string='REGULATION', domain="[('fields.name', '=', 'reglamentacion')]")
	articulos_envase = fields.Many2one('js_parameterization.value', string='PACKAGE ITEMS NUM', domain="[('fields.name', '=', 'articulos_envase')]")
	deporte = fields.Many2one('js_parameterization.value', string='SPORT', domain="[('fields.name', '=', 'deporte')]")
	uso = fields.Many2one('js_parameterization.value', string='USE', domain="[('fields.name', '=', 'uso')]")
	composicion_material = fields.Many2one('js_parameterization.value', string='COMPOSITION/MATERIAL', domain="[('fields.name', '=', 'composicion_material')]")
	tipo_producto = fields.Many2one('js_parameterization.value', string='PRODUCT TYPE', domain="[('fields.name', '=', 'tipo_producto')]")

	# PALAS
	pala_construccion = fields.Many2one('js_parameterization.value', string='STRUCTURE', domain="[('fields.name', '=', 'pala_construccion')]")
	pala_tipo_juego = fields.Many2one('js_parameterization.value', string='GAME TYPE', domain="[('fields.name', '=', 'pala_tipo_juego')]")
	pala_cara = fields.Many2one('js_parameterization.value', string='FACE', domain="[('fields.name', '=', 'pala_cara')]")
	pala_forma = fields.Many2one('js_parameterization.value', string='SHAPE', domain="[('fields.name', '=', 'pala_forma')]")
	pala_nucleo = fields.Many2one('js_parameterization.value', string='CORE', domain="[('fields.name', '=', 'pala_nucleo')]")
	pala_agarre = fields.Many2one('js_parameterization.value', string='GRIP', domain="[('fields.name', '=', 'pala_agarre')]")
	pala_balance = fields.Many2one('js_parameterization.value', string='BALANCE', domain="[('fields.name', '=', 'pala_balance')]")
	pala_perfil = fields.Many2one('js_parameterization.value', string='PROFILE', domain="[('fields.name', '=', 'pala_perfil')]")
	pala_acabado = fields.Many2one('js_parameterization.value', string='FINISH', domain="[('fields.name', '=', 'pala_acabado')]")
	pala_tamano_cabeza = fields.Many2one('js_parameterization.value', string='HEAD SIZE', domain="[('fields.name', '=', 'pala_tamano_cabeza')]")
	pala_ancho = fields.Many2one('js_parameterization.value', string='WIDTH', domain="[('fields.name', '=', 'pala_ancho')]")
	pala_longitud = fields.Many2one('js_parameterization.value', string='LENGTH', domain="[('fields.name', '=', 'pala_longitud')]")

	# RAQUETAS
	raqueta_construccion = fields.Many2one('js_parameterization.value', string='STRUCTURE', domain="[('fields.name', '=', 'raqueta_construccion')]")
	raqueta_tension_cordaje = fields.Many2one('js_parameterization.value', string='STRING TENSION', domain="[('fields.name', '=', 'raqueta_tension_cordaje')]")
	raqueta_tipo_juego = fields.Many2one('js_parameterization.value', string='GAME TYPE', domain="[('fields.name', '=', 'raqueta_tipo_juego')]")
	raqueta_balance = fields.Many2one('js_parameterization.value', string='BALANCE', domain="[('fields.name', '=', 'raqueta_balance')]")
	raqueta_tamano_cabeza = fields.Many2one('js_parameterization.value', string='HEAD SIZE', domain="[('fields.name', '=', 'raqueta_tamano_cabeza')]")
	raqueta_perfil = fields.Many2one('js_parameterization.value', string='PROFILE', domain="[('fields.name', '=', 'raqueta_perfil')]")
	raqueta_longitud = fields.Many2one('js_parameterization.value', string='LENGTH', domain="[('fields.name', '=', 'raqueta_longitud')]")
	raqueta_marco = fields.Many2one('js_parameterization.value', string='FRAME', domain="[('fields.name', '=', 'raqueta_marco')]")

	# REDES
	redes_tratamiento = fields.Many2one('js_parameterization.value', string='TREATMENT', domain="[('fields.name', '=', 'redes_tratamiento')]")
	redes_malla = fields.Many2one('js_parameterization.value', string='MESH', domain="[('fields.name', '=', 'redes_malla')]")
	redes_requisitos = fields.Many2one('js_parameterization.value', string='REQUIREMENTS', domain="[('fields.name', '=', 'redes_requisitos')]")

	# EQUIPAMIENTO
	equipamiento_requisitos = fields.Many2one('js_parameterization.value', string='REQUIREMENTS', domain="[('fields.name', '=', 'equipamiento_requisitos')]")
	equipamiento_seccion_tubo = fields.Many2one('js_parameterization.value', string='TUBE SECTION', domain="[('fields.name', '=', 'equipamiento_seccion_tubo')]")
	equipamiento_tratamiento = fields.Many2one('js_parameterization.value', string='TREATMENT', domain="[('fields.name', '=', 'equipamiento_tratamiento')]")

	# TEXTIL
	textil_tipo_prenda = fields.Many2one('js_parameterization.value', string='GARMENT TYPE', domain="[('fields.name', '=', 'textil_tipo_prenda')]")

	@api.model
	def get_field_id(self, field_name):
		self.env.cr.execute("SELECT id FROM ir_model_fields WHERE name LIKE %s LIMIT 1", (field_name,))
		result = self.env.cr.fetchone()
		return result[0] if result else False

	@api.model
	def template_fields_get(self, template_id=None):
		fields_set = set()
		view_id = self.env.ref(PRODUCT_PARAM_FORM_ID)
		parameterization_template_id = template_id or getattr(self, PARAM_TEMPLATE_FIELD)

		for group in xee.fromstring(str(view_id.arch_base)).findall('%s//group//group' % PARAM_FIELDS_XPATH):
			group_attrs = safe_eval(group.attrib.get('attrs', '{}'))
			groups_attr_invisible = group_attrs.get('invisible')
			group_fields = tuple([field.attrib.get('name') for field in group.findall('.//field')])

			if parameterization_template_id and groups_attr_invisible and group_fields:
				for domain_item in groups_attr_invisible:
					is_valid_domain = type(domain_item) in (list, tuple) and len(domain_item)==3
					is_param_domain = is_valid_domain and domain_item[0] == PARAM_TEMPLATE_FIELD and domain_item[1] == '!='
					if is_param_domain and parameterization_template_id == domain_item[2]:
						fields_set |= set(group_fields)

			# Generic group fields
			elif not groups_attr_invisible:
				fields_set |= set(group_fields)

		return tuple(fields_set)

	@api.model
	def template_fields_dict(self):
		fields_dict = dict()
		for field_name in self.template_fields_get():
			if hasattr(self, field_name):
				fields_dict.update({ self.get_field_id(field_name): getattr(self, field_name).id })
		return fields_dict

	@api.model
	def is_empty(self):
		parameterization_dict = self.template_fields_dict()
		parameterization_vals = parameterization_dict.values()
		return parameterization_vals.count(False) == len(parameterization_vals)

	@api.multi
	def template_fields_reset(self, values):
		view_id = self.env.ref(PRODUCT_PARAM_FORM_ID)
		all_param_fields = [tag.attrib.get('name') for tag in xee.fromstring(str(view_id.arch_base)).findall('%s//field' % PARAM_FIELDS_XPATH)]

		# If parameterization template changed, empty not applicable fields
		# We did this instead of delete asociated parameterization to avoid fill generic fields again
		if values.get(PARAM_TEMPLATE_FIELD):
			for record in self:
				if record.parameterization_template != values[PARAM_TEMPLATE_FIELD]:
					record_applicable_fields = record.template_fields_get(values[PARAM_TEMPLATE_FIELD])
					fields_to_reset = [field for field in all_param_fields if field not in record_applicable_fields]
					for field_name in fields_to_reset:
						values.update({ field_name: False })

		return values

	@api.multi
	def go_to_product(self):
		self.ensure_one()  # One record expected
		return {  # Go to product form
			'view_type': 'form',
			'view_mode': 'form',
			'res_id': self.product_tmpl_id.id,
			'res_model': 'product.template',
			'type': 'ir.actions.act_window'
		}

	#override
	@api.model
	def create(self, values):
		param = super(ProductParameterization, self).create(values)
		if param and not param.is_empty(): self.product_tmpl_id.compute_parameterization_percent()
		return param

	#override
	@api.multi
	def write(self, values):
		values = self.template_fields_reset(values)
		super(ProductParameterization, self).write(values)
		self.product_tmpl_id.compute_parameterization_percent()
		return True

	#override
	@api.multi
	def unlink(self):
		product_tmpl_ids = self.mapped('product_tmpl_id').ids
		if super(ProductParameterization, self).unlink()
			self.env['product.template'].browse(product_tmpl_ids).compute_parameterization_percent()
		return True