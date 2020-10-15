# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from unidecode import unidecode
import lxml.etree as xee
import copy
import re

class ParameterizationType(models.Model):
    _name = 'js_parameterization.type'
    _description = "Parameterization Types"
    _sql_constraints = [('parameterization_type_unique', 'unique(name)', 'Type must be unique in parameterization!')]
    _order = 'sequence, id'
    name = fields.Char(required=True, translate=False)
    sequence = fields.Integer(help="Determine the display order", default=10)

class ParameterizationField(models.Model):
    _name = 'js_parameterization.field'
    _description = 'Parameterization Fields'
    _inherit = 'ir.model.fields'
    _order = 'sequence, id'

    def _set_mod_filter(self):
        # Get model ids for fields
        model_ids = self.env['ir.model'].sudo().search([('model', 'in', ['product.template.parameterization', 'product.product.parameterization'])])
        # Set domain to this ids
        return [('id', 'in', model_ids.ids)]

    def _set_next_sequence(self):
        # Get higher sequence number
        higher_sequence = self.search([], limit=1, order='sequence DESC').sequence
        # Return next number or 1
        return higher_sequence + 1 if higher_sequence else 1

    sequence = fields.Integer(default=_set_next_sequence, copy=False)
    parameterization_type = fields.Many2one('js_parameterization.type', ondelete='restrict', required=False)
    name = fields.Char(copy=False)
    model_id = fields.Many2one(domain=_set_mod_filter)
    selection_vals = fields.Many2many('js_parameterization.value', 'js_parameterization_field_js_parameterization_value_rel', 'js_parameterization_field_id', 'js_parameterization_value_id')
    filter_vals = fields.Boolean()

    #override
    @api.multi
    def name_get(self):
        return [(record.id, record.name) for record in self]

    #override
    @api.model
    def _get_field_types(self):
        return [  # Get field types
            ('char', _('Text')),
            ('text', _('Long Text')),
            ('date', _('Date')),
            ('float', _('Decimal')),
            ('monetary', _('Monetary')),
            ('integer', _('Integer')),
            ('many2one', _('Many2one')),
            ('many2many', _('Many2many')),
            ('js_many2one', _('Select')), # Special selection for parameterization values
            ('js_many2many', _('Multiselect')) # Special multi-selection for parameterization values
        ]

    #override
    @api.onchange('related')
    def _onchange_related(self):
        if self.related:
            try:
                # Set relation
                field = self._related_field()
                self.relation = field.comodel_name
                self.translate = field.translate
                self.ttype = field.type
                self.readonly = True
                self.store = False
                self.copy = False
            except:
                return {
                    'warning': {
                        'title': _("Warning"),
                        'message': _("Relation not valid on selected model!")
                    }
                }

    #override
    @api.onchange('name', 'ttype', 'model_id', 'relation')
    def _onchange_ttype(self):
        special_values_model = 'js_parameterization.value'
        # Call super overrided method first
        super(ParameterizationField, self)._onchange_ttype()
        # If is relational field set relation to js_parameterization.value
        if self.ttype in ('js_many2one', 'js_many2many'):
            self.relation = special_values_model
        # If is many2many override relation_table name, Odoo by default creates
        # the table starting with x_modelname and wee need different tables for each field
        if self.name and self.model_id and self.ttype == 'js_many2many':
            self.relation_table = "%s_%s_rel" % (self.name, special_values_model.replace('.', '_'))

    #private
    @api.onchange('parameterization_type', 'field_description')
    def _set_name_from_label(self):
        if self.field_description:
            # Uppercase field_description
            self.field_description = self.field_description.upper()
        if not self._origin: # Only on create mode
            slug = 'x' # Restore original preffix
            if self.parameterization_type: # If var is False, nothing to do
                slug += '_' + unidecode(self.parameterization_type.name).lower() # Change accentuated chars and convert to lowercase
            if self.field_description: # If var is False, nothing to do
                slug += '_' + unidecode(self.field_description).lower() # Change accentuated chars and convert to lowercase
            slug = re.sub(r"[^\w\s]", '', slug) # Remove all non-word characters (everything except numbers and letters)
            slug = re.sub(r"\s+", '_', slug) # Replace all runs of whitespace with a single dash
            self.name = slug # Update field

    #private
    @api.model
    def _createFieldsXml(self):
        # import web_pdb; web_pdb.set_trace()
        parameterization_product_view = self.env.ref('js_parameterization.parameterization_product_form_view')
        parameterization_variant_view = self.env.ref('js_parameterization.parameterization_variant_form_view')
        parameterization_product_search = self.env.ref('js_parameterization.parameterization_product_search_by_field')
        parameterization_variant_search = self.env.ref('js_parameterization.parameterization_variant_search_by_field')
        # Parse XML string
        parser = xee.XMLParser(remove_blank_text=True)
        pdoc = xee.fromstring(parameterization_product_view.arch_base, parser=parser)
        vdoc = xee.fromstring(parameterization_variant_view.arch_base, parser=parser)
        psea = xee.fromstring(parameterization_product_search.arch_base, parser=parser)
        vsea = xee.fromstring(parameterization_variant_search.arch_base, parser=parser)
        # Get fields container
        pdoc_parameterization_section = pdoc.find('.//div[@id="parameterization_fields"]/group')
        vdoc_parameterization_section = vdoc.find('.//div[@id="parameterization_fields"]/group')
        # Remove all sub-elements (childs)
        pdoc_parameterization_section.clear()
        vdoc_parameterization_section.clear()
        psea.clear()
        psea.set('string', _("Product Parameterization Fields"))
        psea_field_search = xee.SubElement(psea, 'field')
        psea_field_search.set('name', 'product_id')
        vsea.clear()
        vsea.set('string', _("Variant Parameterization Fields"))
        vsea_field_search = xee.SubElement(vsea, 'field')
        vsea_field_search.set('name', 'product_id')
        # Regenerate fields XML for each type
        for type in list([(False, _('Generic'))] + [(type.id, type.name) for type in self.env['js_parameterization.type'].search([])]):
            # Get fields for this type
            fields_for_type = self.env['js_parameterization.field'].search([('parameterization_type', '=', type[0])])
            # If have fields
            if len(fields_for_type):
                # Create fields group
                pdoc_field_group = xee.SubElement(pdoc_parameterization_section, 'group')
                vdoc_field_group = xee.SubElement(vdoc_parameterization_section, 'group')
                # Put condition to hide field if other type is selected
                if type[0]:
                    pdoc_field_group.set('attrs', "{ 'invisible': [('parameterization_template', '!=', %s)] }" % type[0])
                    vdoc_field_group.set('attrs', "{ 'invisible': [('parameterization_template', '!=', %s)] }" % type[0])
                # If have name, set it
                if type[1]:
                    pdoc_field_group.set('string', type[1])
                    vdoc_field_group.set('string', type[1])
                # Create fields XML
                for field in fields_for_type:
                    if field.model_id.model == 'product.template.parameterization':
                        doc_field_input = xee.SubElement(pdoc_field_group, 'field')
                        doc_field_search = xee.SubElement(psea, 'field')
                    else:
                        doc_field_input = xee.SubElement(vdoc_field_group, 'field')
                        doc_field_search = xee.SubElement(vsea, 'field')
                    doc_field_input.set('name', field.name)
                    doc_field_input.set('string', field.field_description)
                    if field.ttype in ('many2many', 'js_many2many'):
                        doc_field_input.set('widget', 'many2many_tags')
                    if field.ttype in ('js_many2one', 'js_many2many'):
                        doc_field_input.set('options', "{ 'no_open': True, 'no_create': True }")
                        field_domain = "['&', ('parameterization_type', '=', parameterization_template), " if field.filter_vals else "["
                        doc_field_input.set('domain', field_domain + "('id', 'in', %s)]" % field.selection_vals.ids)
                    #if field.index: # If is indexed field
                    doc_field_search.set('name', field.name)
                    doc_field_search.set('string', field.field_description if not type[0] else field.field_description + ' [%s]' % type[1].upper())
        # Save XML to database
        parameterization_product_view.arch_base = xee.tostring(pdoc, pretty_print=True)
        parameterization_variant_view.arch_base = xee.tostring(vdoc, pretty_print=True)
        parameterization_product_search.arch_base = xee.tostring(psea, pretty_print=True)
        parameterization_variant_search.arch_base = xee.tostring(vsea, pretty_print=True)
        return True

    #private
    @api.model
    def _resetXml(self):
        for view in ('parameterization_product_form_view', 'parameterization_product_search_by_field', 'parameterization_variant_form_view', 'parameterization_variant_search_by_field'):
            # Get view object
            parameterization_view = self.env.ref('js_parameterization.' + view).sudo()
            # Get and parse view XML
            doc = xee.fromstring(parameterization_view.arch_base)
            # In search view clear all
            if (view in ('parameterization_product_search_by_field', 'parameterization_variant_search_by_field')):
                doc.clear()
            # On others clear group
            else: 
                doc.find('.//div[@id="parameterization_fields"]/group').clear()
            # Save to field
            parameterization_view.arch_base = xee.tostring(doc)

    #private
    @staticmethod
    def _transformValues(model_values):
        values = copy.copy(model_values)
        if values.get('ttype', False) and values['ttype'].startswith('js_'):
            values['ttype'] = values['ttype'].replace('js_', '')
        return values

    #override
    @api.model
    def create(self, values):
        try:
            model_values = copy.copy(values)
            # Create base field for the model
            self.env['ir.model.fields'].sudo().create(self._transformValues(model_values))
            # Create parameterization field
            result = super(ParameterizationField, self).create(model_values)
            if result:
                self._createFieldsXml()
        except Exception, exception:
            raise exception
        return result

    #override
    @api.multi
    def write(self, values):
        updating_secuence = (values.get('sequence') and len(values) == 1)
        model_values = copy.copy(values)
        # Reset XML to make changes
        if not updating_secuence:
            self._resetXml()
        # Loop records
        for record in self:
            try:
                # Write model base field
                if not updating_secuence:
                    custom_field = self.env['ir.model.fields'].sudo().search([('name', '=', record.name), ('state', '=', 'manual')])
                    custom_field.ensure_one() # One record expected, if more abort
                    custom_field.write(self._transformValues(model_values))
                # Write parameterization field
                super(ParameterizationField, record).write(model_values)
            except:
                pass
        # Write fields to XML
        if not updating_secuence:
            self._createFieldsXml()
        return True

    #override
    @api.multi
    def unlink(self):
        # Reset XML to make changes
        self._resetXml()
        # Loop records
        for record in self:
            try:
                # Save name to unlink base field
                record_name = record.name
                # Delete parameterization field
                super(ParameterizationField, record).unlink()
                # Unlink model base field
                custom_field = self.env['ir.model.fields'].sudo().search([('name', '=', record_name), ('state', '=', 'manual')])
                custom_field.ensure_one()  # One record expected, if more abort
                custom_field.with_context(_force_unlink=True).unlink()
            except Exception, exception:
                raise exception
        # Write fields to XML
        self._createFieldsXml()
        return True

class ParameterizationValue(models.Model):
    _name = 'js_parameterization.value'
    _description = "Parameterization Values"
    _order = 'name, parameterization_type'
    _sql_constraints = [('parameterization_value_unique', 'unique(name, parameterization_type)', 'Value must be unique in parameterization type!')]

    name = fields.Char(required=True, translate=True)
    parameterization_type = fields.Many2one('js_parameterization.type', ondelete='cascade', required=False)
    fields = fields.Many2many('js_parameterization.field', 'js_parameterization_field_js_parameterization_value_rel', 'js_parameterization_value_id', 'js_parameterization_field_id')

    #override
    @api.multi
    def name_get(self):
        result = []
        for record in self:
            record_list = [record.id, record.name]
            if (record.parameterization_type):
                record_list[1] += ' [%s]' % record.parameterization_type.name.upper()
            result.append(tuple(record_list))
        return result

    #override
    @api.model
    def create(self, values):
        result = super(ParameterizationValue, self).create(values)
        if result:
            self.env['js_parameterization.field']._createFieldsXml()
            return result

    #override
    @api.multi
    def write(self, values):
        super(ParameterizationValue, self).write(values)
        self.env['js_parameterization.field']._createFieldsXml()
        return True

    #override
    @api.multi
    def unlink(self):
        super(ParameterizationValue, self).unlink()
        self.env['js_parameterization.field']._createFieldsXml()
        return True
