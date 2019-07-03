# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
from unidecode import unidecode
import lxml.etree as xee
import re

class CategorizationType(models.Model):
    _name = 'js_categorization.type'
    _description = "Categorization Types"
    _sql_constraints = [('categorization_type_unique', 'unique(name)', 'Type must be unique in categorization!')]
    _order = 'id, sequence'
    name = fields.Char(required=True, translate=False)
    sequence = fields.Integer(help="Determine the display order", default=10)

    @api.onchange('name')
    def name_capitalize(self):
        if self.name:
            # Capitalize name
            self.name = self.name.capitalize()

class CategorizationField(models.Model):
    _name = 'js_categorization.field'
    _description = 'Categorization Fields'
    _inherit = 'ir.model.fields'
    _order = 'id, sequence'

    def _set_mod_filter(self):
        # Get model ids for fields
        model_ids = self.env['ir.model'].sudo().search([('model', 'in', ['product.template.categorization',  'product.product.categorization'])])
        # Set domain to this ids
        return [('id', 'in', model_ids.ids)]

    sequence = fields.Integer(default=100)
    categorization_type = fields.Many2one('js_categorization.type', ondelete='restrict', required=False)
    name = fields.Char(copy=False)
    model_id = fields.Many2one(domain=_set_mod_filter)
    selection_vals = fields.Many2many('js_categorization.value', string='Values')
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')

    @api.model
    def _get_field_types(self):
        return [ # Get field types
            ('char', _('Text')),
            ('text', _('Long Text')),
            ('date', _('Date')),
            ('float', _('Decimal')),
            ('monetary', _('Monetary')),
            ('integer', _('Integer')),
            ('many2one', _('Select')), # Special selection for categorization values
            ('many2many', _('Multiselect')) # Special multi-selection for categorization values
        ]

    @api.onchange('field_description')
    def _set_name_from_label(self):
        if self.field_description:
            # Uppercase field_description
            self.field_description = self.field_description.upper()
        if not self._origin: # Only on create mode
            self.name = 'x_' # Restore original value
            if self.field_description: # If var is False, nothing to do
                slug = unidecode(self.field_description).lower() # Change accentuated chars and convert to lowercase
                slug = re.sub(r"[^\w\s]", '', slug) # Remove all non-word characters (everything except numbers and letters)
                slug = re.sub(r"\s+", '_', slug) # Replace all runs of whitespace with a single dash
                self.name = 'x_' + slug # Update field

    @api.onchange('related')
    def _onchange_related(self):
        if self.related:
            try:
                # Set relation
                field = self._related_field()
                self.relation = field.comodel_name
                # Set defaults
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

    @api.model
    def createFieldsXml(self):
        # import web_pdb; web_pdb.set_trace()
        categorization_product_view = self.env.ref('js_categorization.categorization_product_form_view')
        categorization_variant_view = self.env.ref('js_categorization.categorization_variant_form_view')
        categorization_product_search = self.env.ref('js_categorization.categorization_product_search_by_field')
        categorization_variant_search = self.env.ref('js_categorization.categorization_variant_search_by_field')
        # Parse XML string
        parser = xee.XMLParser(remove_blank_text=True)
        pdoc = xee.fromstring(categorization_product_view.arch_base, parser=parser)
        vdoc = xee.fromstring(categorization_variant_view.arch_base, parser=parser)
        psea = xee.fromstring(categorization_product_search.arch_base, parser=parser)
        vsea = xee.fromstring(categorization_variant_search.arch_base, parser=parser)
        # Get fields container
        pdoc_categorization_section = pdoc.find('.//div[@id="categorization_fields"]/group')
        vdoc_categorization_section = vdoc.find('.//div[@id="categorization_fields"]/group')
        # Remove all sub-elements (childs)
        pdoc_categorization_section.clear()
        vdoc_categorization_section.clear()
        psea.clear()
        psea.set('string', _("Product Categorization Fields"))
        psea_field_search = xee.SubElement(psea, 'field')
        psea_field_search.set('name', 'product_id')
        vsea.clear()
        vsea.set('string', _("Variant Categorization Fields"))
        vsea_field_search = xee.SubElement(vsea, 'field')
        vsea_field_search.set('name', 'variant_id')
        # Regenerate fields XML for each type
        for type in list([(False, _('Generic'))] + [(type.id, type.name) for type in self.env['js_categorization.type'].search([])]):
            # Get fields for this type
            fields_for_type = self.env['js_categorization.field'].search([('categorization_type', '=', type[0])])
            # If have fields
            if len(fields_for_type):
                # Create fields group
                pdoc_field_group = xee.SubElement(pdoc_categorization_section, 'group')
                vdoc_field_group = xee.SubElement(vdoc_categorization_section, 'group')
                # Put condition to hide field if type is selected
                if type[0]:
                    pdoc_field_group.set('attrs', "{ 'invisible': [('categorization_template', '!=', %s)] }" % (type[0]))
                    vdoc_field_group.set('attrs', "{ 'invisible': [('categorization_template', '!=', %s)] }" % (type[0]))
                # If have name, set it
                if type[1]:
                    pdoc_field_group.set('string', type[1])
                    vdoc_field_group.set('string', type[1])
                # Create fields XML
                for field in fields_for_type:
                    if field.model_id.model == 'product.template.categorization':
                        doc_field_input = xee.SubElement(pdoc_field_group, 'field')
                        doc_field_search = xee.SubElement(psea, 'field')
                    else:
                        doc_field_input = xee.SubElement(vdoc_field_group, 'field')
                        doc_field_search = xee.SubElement(vsea, 'field')
                    doc_field_input.set('name', field.name)
                    doc_field_input.set('string', field.field_description)
                    if field.ttype == 'many2many': # If is many2many field
                        doc_field_input.set('widget', 'many2many_tags')
                    if field.ttype in ('many2one', 'many2many'): # If is many2one or many2many field
                        doc_field_input.set('options', "{'no_open': True, 'no_create': True}")
                        doc_field_input.set('domain', "[('id', 'in', %s)]" % (str(field.selection_vals.ids)))
                    #if field.index: # If is indexed field
                    doc_field_search.set('name', field.name)
                    doc_field_search.set('string', field.field_description)
        # Save XML to database
        categorization_product_view.arch_base = xee.tostring(pdoc, pretty_print=True)
        categorization_variant_view.arch_base = xee.tostring(vdoc, pretty_print=True)
        categorization_product_search.arch_base = xee.tostring(psea, pretty_print=True)
        categorization_variant_search.arch_base = xee.tostring(vsea, pretty_print=True)

    @api.model
    def _resetXml(self):
        for view in ('categorization_product_form_view', 'categorization_product_search_by_field', 'categorization_variant_form_view', 'categorization_variant_search_by_field'):
            # Get view object
            categorization_view = self.env.ref('js_categorization.' + view).sudo()
            # Get and parse view XML
            doc = xee.fromstring(categorization_view.arch_base)
            # In search view clear all
            if (view in ('categorization_product_search_by_field', 'categorization_variant_search_by_field')):
                doc.clear()
            else: # On others clear group
                doc.find('.//div[@id="categorization_fields"]/group').clear()
            # Save to field
            categorization_view.arch_base = xee.tostring(doc)

    @api.model
    def create(self, values):
        try:
            # If is relational field set relation to js_categorization.value
            if values.get('ttype') in ('many2one', 'many2many'):
                values.update({'relation': 'js_categorization.value'})
            # Create base field for the model
            self.env['ir.model.fields'].sudo().create(values)
            # Create categorization field
            result = super(CategorizationField, self).create(values)
            if result:
                # Write to database
                self.env.cr.commit()
                # Write fileds to XML
                self.createFieldsXml()
        except Exception, exception:
            # Not make changes in db
            self.env.cr.rollback()
            raise exception
        return result

    @api.multi
    def write(self, values):
        # Reset XML to make changes
        self._resetXml()
        # Loop records
        for record in self:
            try:
                # Write model base field
                if not (values.get('sequence') and len(values) == 1):
                    custom_field = self.env['ir.model.fields'].sudo().search([('name', '=', record.name), ('state', '=', 'manual')])
                    custom_field.ensure_one() # One record expected, if more abort
                    custom_field.write(values)
                # Write categorization field
                if super(CategorizationField, record).write(values):
                    # Write to database
                    self.env.cr.commit()
            except Exception, exception:
                # Not make changes in db
                self.env.cr.rollback()
                raise exception
        # Write fields to XML
        self.createFieldsXml()
        return True

    @api.multi
    def unlink(self):
        # Reset XML to make changes
        self._resetXml()
        # Loop records
        for record in self:
            try:
                # Save name to unlink base field
                record_name = record.name
                # Delete categorization field
                if super(CategorizationField, record).unlink():
                    # Unlink model base field
                    custom_field = self.env['ir.model.fields'].sudo().search([('name', '=', record_name), ('state', '=', 'manual')])
                    custom_field.ensure_one() # One record expected, if more abort
                    custom_field.with_context(_force_unlink=True).unlink()
                    # Write to database
                    self.env.cr.commit()
            except Exception, exception:
                # Not make changes in db
                self.env.cr.rollback()
                raise exception
        # Write fields to XML
        self.createFieldsXml()
        return True

class CategorizationValue(models.Model):
    _name = 'js_categorization.value'
    _description = "Categorization Values"
    _sql_constraints = [('categorization_value_unique', 'unique(name)', 'Value must be unique in categorization!')]
    name = fields.Char(required=True, translate=True)

    @api.onchange('name')
    def name_to_lower(self):
        if self.name:
            # Lowercase name
            self.name = self.name.lower()
