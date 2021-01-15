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
	
	# [LOIS] Crea el select, no carga las opciones de ningún sitio
	# PARAM_TEMPLATE_FIELD Definition
	parameterization_template = fields.Selection(constants.TEMPLATES_LIST, required=False)

	# TODO
	tipo_producto = fields.Many2one('js_parameterization.value', string='PRODUCT TYPE', domain="[('fields.name', '=', 'tipo_producto')]")
	deporte = fields.Many2one('js_parameterization.value', string='SPORT', domain="[('fields.name', '=', 'deporte')]")
	nivel_habilidad = fields.Many2one('js_parameterization.value', string='SKILL LEVEL', domain="[('fields.name', '=', 'nivel_habilidad')]")
	uso = fields.Many2one('js_parameterization.value', string='USE', domain="[('fields.name', '=', 'uso')]")
	envase = fields.Many2one('js_parameterization.value', string='PACKAGING', domain="[('fields.name', '=', 'envase')]")
	articulos_envase = fields.Many2one('js_parameterization.value', string='PACKAGE ITEMS NUM', domain="[('fields.name', '=', 'articulos_envase')]")
	composicion_material = fields.Many2one('js_parameterization.value', string='COMPOSITION/MATERIAL', domain="[('fields.name', '=', 'composicion_material')]")
	reglamentacion = fields.Many2one('js_parameterization.value', string='REGULATION', domain="[('fields.name', '=', 'reglamentacion')]")
	certificaciones_ensayos = fields.Many2one('js_parameterization.value', string='CERTIFICATIONS/TESTS', domain="[('fields.name', '=', 'certificaciones_ensayos')]")
	coleccion = fields.Many2one('js_parameterization.value', string='COLLECTION', domain="[('fields.name', '=', 'coleccion')]")
	genero = fields.Many2one('js_parameterization.value', string='GENDER', domain="[('fields.name', '=', 'genero')]")

	# PALAS
	pala_construccion = fields.Many2one('js_parameterization.value', string='STRUCTURE', domain="[('fields.name', '=', 'pala_construccion')]")
	pala_tipo_juego = fields.Many2one('js_parameterization.value', string='GAME TYPE', domain="[('fields.name', '=', 'pala_tipo_juego')]")
	pala_cara = fields.Many2one('js_parameterization.value', string='FACE', domain="[('fields.name', '=', 'pala_cara')]")
	pala_forma = fields.Many2one('js_parameterization.value', string='SHAPE', domain="[('fields.name', '=', 'pala_forma')]")
	pala_marco = fields.Many2one('js_parameterization.value', string='FRAME', domain="[('fields.name', '=', 'pala_marco')]")
	pala_nucleo = fields.Many2one('js_parameterization.value', string='CORE', domain="[('fields.name', '=', 'pala_nucleo')]")
	pala_agarre_mango = fields.Many2one('js_parameterization.value', string='HANDLE FIXING', domain="[('fields.name', '=', 'pala_agarre')]")
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

	# BADMINTON
	badminton_perfil = fields.Many2one('js_parameterization.value', string='PROFILE', domain="[('fields.name', '=', 'badminton_perfil')]")
	badminton_tension_cordaje = fields.Many2one('js_parameterization.value', string='STRING TENSION', domain="[('fields.name', '=', 'badminton_tension_cordaje')]")
	badminton_longitud = fields.Many2one('js_parameterization.value', string='LENGTH', domain="[('fields.name', '=', 'badminton_longitud')]")
	badminton_construccion = fields.Many2one('js_parameterization.value', string='STRUCTURE', domain="[('fields.name', '=', 'badminton_construccion')]")
	badminton_tamano_cabeza = fields.Many2one('js_parameterization.value', string='HEAD SIZE', domain="[('fields.name', '=', 'badminton_tamano_cabeza')]")

	# REDES
	redes_tratamiento = fields.Many2one('js_parameterization.value', string='TREATMENT', domain="[('fields.name', '=', 'redes_tratamiento')]")
	redes_malla = fields.Many2one('js_parameterization.value', string='MESH', domain="[('fields.name', '=', 'redes_malla')]")
	redes_requisitos = fields.Many2one('js_parameterization.value', string='REQUIREMENTS', domain="[('fields.name', '=', 'redes_requisitos')]")

	# EQUIPAMIENTO
	equipamiento_requisitos = fields.Many2one('js_parameterization.value', string='REQUIREMENTS', domain="[('fields.name', '=', 'equipamiento_requisitos')]")
	equipamiento_seccion_tubo = fields.Many2one('js_parameterization.value', string='TUBE SECTION', domain="[('fields.name', '=', 'equipamiento_seccion_tubo')]")
	equipamiento_tratamiento = fields.Many2one('js_parameterization.value', string='TREATMENT', domain="[('fields.name', '=', 'equipamiento_tratamiento')]")
	equipamiento_reglamentacion = fields.Many2one('js_parameterization.value', string='REGULATION', domain="[('fields.name', '=', 'equipamiento_reglamentacion')]")

	# TEXTIL
	textil_tipo_prenda = fields.Many2one('js_parameterization.value', string='GARMENT TYPE', domain="[('fields.name', '=', 'textil_tipo_prenda')]")
	textil_formato = fields.Many2one('js_parameterization.value', string='FORMAT', domain="[('fields.name', '=', 'textil_formato')]")
	textil_gramaje = fields.Many2one('js_parameterization.value', string='GRAMMAGE', domain="[('fields.name', '=', 'textil_gramaje')]")
	textil_acabado = fields.Many2one('js_parameterization.value', string='FINISH', domain="[('fields.name', '=', 'textil_acabado')]")
	textil_tratamientos = fields.Many2one('js_parameterization.value', string='TREATMENTS', domain="[('fields.name', '=', 'textil_tratamientos')]")
	textil_diseno = fields.Many2one('js_parameterization.value', string='DESIGN', domain="[('fields.name', '=', 'textil_diseno')]")
	textil_tejido = fields.Many2one('js_parameterization.value', string='TISSUE', domain="[('fields.name', '=', 'textil_tejido')]")
	textil_bolsilllos = fields.Many2one('js_parameterization.value', string='POCKETS', domain="[('fields.name', '=', 'textil_bolsilllos')]")
	textil_patron = fields.Many2one('js_parameterization.value', string='PATTERN', domain="[('fields.name', '=', 'textil_patron')]")
	textil_tipo_bajo = fields.Many2one('js_parameterization.value', string='LOWER FINISHED', domain="[('fields.name', '=', 'textil_tipo_bajo')]")
	textil_tipo_cintura = fields.Many2one('js_parameterization.value', string='WAIST TYPE', domain="[('fields.name', '=', 'textil_tipo_cintura')]")
	textil_tipo_manga = fields.Many2one('js_parameterization.value', string='SLEEVE TYPE', domain="[('fields.name', '=', 'textil_tipo_manga')]")
	textil_tipo_cuello = fields.Many2one('js_parameterization.value', string='NECK TYPE', domain="[('fields.name', '=', 'textil_tipo_cuello')]")
	textil_tipo_cierre = fields.Many2one('js_parameterization.value', string='CLASP TYPE', domain="[('fields.name', '=', 'textil_tipo_cierre')]")
	textil_logo = fields.Many2one('js_parameterization.value', string='LOGO', domain="[('fields.name', '=', 'textil_logo')]")
	textil_interior = fields.Many2one('js_parameterization.value', string='GARMENT INTERIOR', domain="[('fields.name', '=', 'textil_interior')]")

	# CALZADO
	calzado_tipo = fields.Many2one('js_parameterization.value', string='TYPE', domain="[('fields.name', '=', 'calzado_tipo')]")
	calzado_suela = fields.Many2one('js_parameterization.value', string='SOLE', domain="[('fields.name', '=', 'calzado_suela')]")
	calzado_empeine = fields.Many2one('js_parameterization.value', string='INSTEP', domain="[('fields.name', '=', 'calzado_empeine')]")
	calzado_forro_y_plantilla = fields.Many2one('js_parameterization.value', string='LINING AND INSOLE', domain="[('fields.name', '=', 'calzado_forro_y_plantilla')]")
	calzado_cierre = fields.Many2one('js_parameterization.value', string='LOCK', domain="[('fields.name', '=', 'calzado_cierre')]")

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
		if param and not param.is_empty(): param.product_tmpl_id.compute_parameterization_percent()
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
		if super(ProductParameterization, self).unlink():
			self.env['product.template'].browse(product_tmpl_ids).compute_parameterization_percent()
		return True