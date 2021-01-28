# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.tools.safe_eval import safe_eval
from psycopg2.extensions import AsIs
import xml.etree.ElementTree as xee
from .. import constants

PARAM_TEMPLATE_FIELD = 'parameterization_template'
PRODUCT_PARAMETERIZATION = 'product.parameterization'
PARAM_FIELDS_XPATH = './/div[@id="parameterization_fields"]'
PRODUCT_PARAM_FORM_ID = 'js_parameterization.parameterization_product_form_view'

class ParameterizationValue(models.Model):
	_name = 'js_parameterization.value'
	_description = "Parameterization Values"
	_sql_constraints = [('parameterization_value_unique', 'unique(name)', 'Value must be unique in parameterization!')]
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
		for field_type in self.env['ir.model.fields'].search([('model', 'like', 'product.parameterization'), ('name', 'like', field_name)]).mapped('ttype'):
			if field_type == 'many2one':
				parameterization_obj.search([(field_name, '=', value_id)]).write({ field_name: False })
			elif field_type == 'many2many':
				parameterization_obj.search([(field_name, 'in', value_id)]).write({ field_name: [(3, value_id)] })
		return True

	#override
	@api.multi
	def write(self, values):	
		for record in self:
			old_fields = record.fields.ids
			super(ParameterizationValue, record).write(values)
			removed_fields = list(set(old_fields) - set(record.fields.ids))

			for field in self.env['ir.model.fields'].browse(removed_fields):
				self.update_parameterization_relations(record.id, field.name)

		return True

class ProductParameterization(models.Model):
	_name = 'product.parameterization'
	_description = "Product Parameterization"
	_sql_constraints = [('parameterization_product_unique', 'unique(product_tmpl_id)', 'Product must be unique in parameterization!')]
	_rec_name = 'product_tmpl_id' 

	product_tmpl_id = fields.Many2one('product.template', string='Related Product', required=True, ondelete='cascade')
	parameterization_template = fields.Selection(constants.TEMPLATES_LIST, required=False)
	percent_filled = fields.Integer('Parameterization Percent Completed', related='product_tmpl_id.parameterization_percent_filled', store=False)

	# TODO
	tipo_producto = fields.Many2one('js_parameterization.value', string='PRODUCT TYPE', domain=[('fields.name', '=', 'tipo_producto')])
	deporte = fields.Many2many('js_parameterization.value', 'js_parameterization_field_deporte_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='SPORT', domain=[('fields.name', '=', 'deporte')])
	nivel_habilidad = fields.Many2one('js_parameterization.value', string='SKILL LEVEL', domain=[('fields.name', '=', 'nivel_habilidad')])
	uso = fields.Many2one('js_parameterization.value', string='USE', domain=[('fields.name', '=', 'uso')])
	envase = fields.Many2one('js_parameterization.value', string='PACKAGING', domain=[('fields.name', '=', 'envase')])
	articulos_envase = fields.Many2one('js_parameterization.value', string='PACKAGE ITEMS NUM', domain=[('fields.name', '=', 'articulos_envase')])
	composicion_material = fields.Many2many('js_parameterization.value', 'js_parameterization_field_composicion_material_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='COMPOSITION/MATERIAL', domain=[('fields.name', '=', 'composicion_material')])
	certificaciones_ensayos = fields.Many2many('js_parameterization.value', 'js_parameterization_field_certificaciones_ensayos_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='CERTIFICATIONS/TESTS', domain=[('fields.name', '=', 'certificaciones_ensayos')])
	coleccion = fields.Many2one('js_parameterization.value', string='COLLECTION', domain=[('fields.name', '=', 'coleccion')])
	genero = fields.Many2one('js_parameterization.value', string='GENDER', domain=[('fields.name', '=', 'genero')])

	# PALAS
	pala_construccion = fields.Many2one('js_parameterization.value', string='PADEL RACKET STRUCTURE', domain=[('fields.name', '=', 'pala_construccion')])
	pala_tipo_juego = fields.Many2one('js_parameterization.value', string='PADEL RACKET GAME TYPE', domain=[('fields.name', '=', 'pala_tipo_juego')])
	pala_cara = fields.Many2one('js_parameterization.value', string='PADEL RACKET FACE', domain=[('fields.name', '=', 'pala_cara')])
	pala_forma = fields.Many2one('js_parameterization.value', string='PADEL RACKET SHAPE', domain=[('fields.name', '=', 'pala_forma')])
	pala_marco = fields.Many2one('js_parameterization.value', string='PADEL RACKET FRAME', domain=[('fields.name', '=', 'pala_marco')])
	pala_nucleo = fields.Many2one('js_parameterization.value', string='PADEL RACKET CORE', domain=[('fields.name', '=', 'pala_nucleo')])
	pala_agarre_mango = fields.Many2one('js_parameterization.value', string='PADEL RACKET HANDLE FIXING', domain=[('fields.name', '=', 'pala_agarre')])
	pala_balance = fields.Many2one('js_parameterization.value', string='PADEL RACKET BALANCE', domain=[('fields.name', '=', 'pala_balance')])
	pala_perfil = fields.Many2one('js_parameterization.value', string='PADEL RACKET PROFILE', domain=[('fields.name', '=', 'pala_perfil')])
	pala_acabado = fields.Many2one('js_parameterization.value', string='PADEL RACKET FINISH', domain=[('fields.name', '=', 'pala_acabado')])
	pala_ancho = fields.Many2one('js_parameterization.value', string='PADEL RACKET WIDTH', domain=[('fields.name', '=', 'pala_ancho')])
	pala_longitud = fields.Many2one('js_parameterization.value', string='PADEL RACKET LENGTH', domain=[('fields.name', '=', 'pala_longitud')])

	# RAQUETAS TENIS
	raqueta_construccion = fields.Many2one('js_parameterization.value', string='TENNIS RACKET STRUCTURE', domain=[('fields.name', '=', 'raqueta_construccion')])
	raqueta_tension_cordaje = fields.Many2one('js_parameterization.value', string='TENNIS RACKET STRING TENSION', domain=[('fields.name', '=', 'raqueta_tension_cordaje')])
	raqueta_tipo_juego = fields.Many2one('js_parameterization.value', string='TENNIS RACKET GAME TYPE', domain=[('fields.name', '=', 'raqueta_tipo_juego')])
	raqueta_balance = fields.Many2one('js_parameterization.value', string='TENNIS RACKET BALANCE', domain=[('fields.name', '=', 'raqueta_balance')])
	raqueta_tamano_cabeza = fields.Many2one('js_parameterization.value', string='TENNIS RACKET HEAD SIZE', domain=[('fields.name', '=', 'raqueta_tamano_cabeza')])
	raqueta_perfil = fields.Many2one('js_parameterization.value', string='TENNIS RACKET PROFILE', domain=[('fields.name', '=', 'raqueta_perfil')])
	raqueta_longitud = fields.Many2one('js_parameterization.value', string='TENNIS RACKET LENGTH', domain=[('fields.name', '=', 'raqueta_longitud')])
	raqueta_marco = fields.Many2one('js_parameterization.value', string='TENNIS RACKET FRAME', domain=[('fields.name', '=', 'raqueta_marco')])

	# RAQUETAS BADMINTON
	badminton_perfil = fields.Many2one('js_parameterization.value', string='BADMINTON RACKET PROFILE', domain=[('fields.name', '=', 'badminton_perfil')])
	badminton_tension_cordaje = fields.Many2one('js_parameterization.value', string='BADMINTON RACKET STRING TENSION', domain=[('fields.name', '=', 'badminton_tension_cordaje')])
	badminton_longitud = fields.Many2one('js_parameterization.value', string='BADMINTON RACKET LENGTH', domain=[('fields.name', '=', 'badminton_longitud')])
	badminton_construccion = fields.Many2one('js_parameterization.value', string='BADMINTON RACKET STRUCTURE', domain=[('fields.name', '=', 'badminton_construccion')])
	badminton_tamano_cabeza = fields.Many2one('js_parameterization.value', string='BADMINTON RACKET HEAD SIZE', domain=[('fields.name', '=', 'badminton_tamano_cabeza')])

	# REDES
	redes_tratamiento = fields.Many2many('js_parameterization.value', 'js_parameterization_field_redes_tratamiento_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='NET TREATMENT', domain=[('fields.name', '=', 'redes_tratamiento')])
	redes_malla = fields.Many2one('js_parameterization.value', string='NET MESH', domain=[('fields.name', '=', 'redes_malla')])
	redes_requisitos = fields.Many2many('js_parameterization.value', 'js_parameterization_field_redes_requisitos_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='NET REQUIREMENTS', domain=[('fields.name', '=', 'redes_requisitos')])

	# EQUIPAMIENTO
	equipamiento_requisitos = fields.Many2many('js_parameterization.value', 'js_parameterization_field_equipamiento_requisitos_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='EQUIPMENT REQUIREMENTS', domain=[('fields.name', '=', 'equipamiento_requisitos')])
	equipamiento_seccion_tubo = fields.Many2many('js_parameterization.value', 'js_parameterization_field_equipamiento_seccion_tubo_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='EQUIPMENT TUBE SECTION', domain=[('fields.name', '=', 'equipamiento_seccion_tubo')])
	equipamiento_tratamiento = fields.Many2many('js_parameterization.value', 'js_parameterization_field_equipamiento_tratamiento_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='EQUIPMENT TREATMENT', domain=[('fields.name', '=', 'equipamiento_tratamiento')])
	equipamiento_reglamentacion = fields.Many2many('js_parameterization.value', 'js_parameterization_field_equipamiento_reglamentacion_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='EQUIPMENT REGULATION', domain=[('fields.name', '=', 'equipamiento_reglamentacion')])

	# TEXTIL
	textil_tipo_prenda = fields.Many2one('js_parameterization.value', string='TEXTIL GARMENT TYPE', domain=[('fields.name', '=', 'textil_tipo_prenda')])
	textil_formato = fields.Many2one('js_parameterization.value', string='TEXTIL FORMAT', domain=[('fields.name', '=', 'textil_formato')])
	textil_gramaje = fields.Many2one('js_parameterization.value', string='TEXTIL GRAMMAGE', domain=[('fields.name', '=', 'textil_gramaje')])
	textil_acabado = fields.Many2many('js_parameterization.value', 'js_parameterization_field_textil_acabado_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='TEXTIL FINISH', domain=[('fields.name', '=', 'textil_acabado')])
	textil_tratamiento = fields.Many2many('js_parameterization.value', 'js_parameterization_field_textil_tratamiento_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='TEXTIL TREATMENT', domain=[('fields.name', '=', 'textil_tratamiento')])
	textil_diseno = fields.Many2one('js_parameterization.value', string='TEXTIL DESIGN', domain=[('fields.name', '=', 'textil_diseno')])
	textil_tejido = fields.Many2many('js_parameterization.value', 'js_parameterization_field_textil_tejido_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='TEXTIL TISSUE', domain=[('fields.name', '=', 'textil_tejido')])
	textil_bolsilllos = fields.Many2many('js_parameterization.value', 'js_parameterization_field_textil_bolsilllos_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='TEXTIL POCKETS', domain=[('fields.name', '=', 'textil_bolsilllos')])
	textil_patron = fields.Many2one('js_parameterization.value', string='TEXTIL PATTERN', domain=[('fields.name', '=', 'textil_patron')])
	textil_tipo_bajo = fields.Many2one('js_parameterization.value', string='TEXTIL LOWER FINISHED', domain=[('fields.name', '=', 'textil_tipo_bajo')])
	textil_tipo_cintura = fields.Many2one('js_parameterization.value', string='TEXTIL WAIST TYPE', domain=[('fields.name', '=', 'textil_tipo_cintura')])
	textil_tipo_manga = fields.Many2one('js_parameterization.value', string='TEXTIL SLEEVE TYPE', domain=[('fields.name', '=', 'textil_tipo_manga')])
	textil_tipo_cuello = fields.Many2one('js_parameterization.value', string='TEXTIL NECK TYPE', domain=[('fields.name', '=', 'textil_tipo_cuello')])
	textil_tipo_cierre = fields.Many2one('js_parameterization.value', string='TEXTIL CLASP TYPE', domain=[('fields.name', '=', 'textil_tipo_cierre')])
	textil_logo = fields.Many2one('js_parameterization.value', string='TEXTIL LOGO', domain=[('fields.name', '=', 'textil_logo')])
	textil_interior = fields.Many2one('js_parameterization.value', string='TEXTIL GARMENT INTERIOR', domain=[('fields.name', '=', 'textil_interior')])

	# CALZADO
	calzado_tipo = fields.Many2one('js_parameterization.value', string='FOOTWEAR TYPE', domain=[('fields.name', '=', 'calzado_tipo')])
	calzado_suela = fields.Many2one('js_parameterization.value', string='FOOTWEAR SOLE', domain=[('fields.name', '=', 'calzado_suela')])
	calzado_empeine = fields.Many2one('js_parameterization.value', string='FOOTWEAR INSTEP', domain=[('fields.name', '=', 'calzado_empeine')])
	calzado_forro_y_plantilla = fields.Many2one('js_parameterization.value', string='FOOTWEAR LINING AND INSOLE', domain=[('fields.name', '=', 'calzado_forro_y_plantilla')])
	calzado_cierre = fields.Many2one('js_parameterization.value', string='FOOTWEAR LOCK', domain=[('fields.name', '=', 'calzado_cierre')])

	# RAQUETAS TENIS MESA
	raqueta_tenis_mesa_caras = fields.Many2many('js_parameterization.value', 'js_parameterization_field_raqueta_tenis_mesa_caras_rel', 'js_product_parameterization_id', 'js_parameterization_value_id', string='TABLE TENNIS RACKET TYPE OF FACES', domain=[('fields.name', '=', 'raqueta_tenis_mesa_caras')])
	raqueta_tenis_mesa_num_laminas = fields.Many2one('js_parameterization.value', string='TABLE TENNIS RACKET NO. OF SHEETS', domain=[('fields.name', '=', 'raqueta_tenis_mesa_num_laminas')])
	raqueta_tenis_mesa_grosor_lamina = fields.Many2one('js_parameterization.value', string='TABLE TENNIS RACKET SHEET THICKNESS', domain=[('fields.name', '=', 'raqueta_tenis_mesa_grosor_lamina')])
	raqueta_tenis_mesa_calidad = fields.Many2one('js_parameterization.value', string='TABLE TENNIS RACKET QUALITY', domain=[('fields.name', '=', 'raqueta_tenis_mesa_calidad')])

	@api.model
	def fields_get(self, allfields=None, attributes=None):
	    res = super(ProductParameterization, self).fields_get(allfields, attributes=attributes)
	    # Hide this fields on search filters
	    for field in ['create_date', 'create_uid', 'write_date', 'write_uid', 'product_tmpl_id', 'parameterization_template']:
	        if res.get(field):
	           res.get(field)['searchable'] = False
	    return res

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
				field_id = self.get_field_id(field_name)
				fields_dict.update({ field_id: getattr(self, field_name).ids })
		return fields_dict

	@api.model
	def is_empty(self):
		parameterization_dict = self.template_fields_dict()
		parameterization_vals = parameterization_dict.values()
		return parameterization_vals.count([]) == len(parameterization_vals)

	@api.multi
	def template_fields_reset(self, values):
		self.ensure_one()
		view_id = self.env.ref(PRODUCT_PARAM_FORM_ID)
		all_param_fields = [tag.attrib.get('name') for tag in xee.fromstring(str(view_id.arch_base)).findall('%s//field' % PARAM_FIELDS_XPATH)]

		# If parameterization template changed, empty not applicable fields
		# We did this instead of delete asociated parameterization to avoid fill generic fields again
		if values.get(PARAM_TEMPLATE_FIELD):
			if self.parameterization_template != values[PARAM_TEMPLATE_FIELD]:
				record_applicable_fields = self.template_fields_get(values[PARAM_TEMPLATE_FIELD])
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
		for record in self:
			values = record.template_fields_reset(values)
			super(ProductParameterization, record).write(values)
			record.product_tmpl_id.compute_parameterization_percent()
		return True

	#override
	@api.multi
	def unlink(self):
		product_tmpl_ids = self.mapped('product_tmpl_id').ids
		if super(ProductParameterization, self).unlink():
			self.env['product.template'].browse(product_tmpl_ids).compute_parameterization_percent()
		return True