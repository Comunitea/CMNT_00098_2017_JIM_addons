# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
import lxml.etree as xee
import unidecode
import re

class CategorizationType(models.Model):
    _name = 'js_categorization.type'
    _description = "Categorization Types"
    _sql_constraints = [('categorization_type_unique', 'unique(name)', 'Type must be unique in categorization!')]
    _order = 'sequence, name, id'
    name = fields.Char(required=True, translate=False)
    sequence = fields.Integer(help="Determine the display order", default=10)

    @api.onchange('name')
    def name_capitalize(self):
        if self.name:
            self.name = str(self.name).capitalize()

class CategorizationField(models.Model):
    _name = 'js_categorization.field'
    _description = 'Categorization Fields'
    _inherit = 'ir.model.fields'
    _order = 'sequence, field_description, id'

    def _set_mod_default(self):
        model_ids = self.env['ir.model'].sudo().search([('model', 'in', ['product.template',  'product.product'])])
        return [('id', 'in', model_ids.ids)]

    sequence = fields.Integer(help="Determine the display order", default=100)
    categorization_type = fields.Many2one('js_categorization.type', ondelete='restrict', string='Cat. Type', required=False)
    name = fields.Char(copy=False)
    model_id = fields.Many2one(domain=_set_mod_default)
    selection_vals = fields.Many2many('js_categorization.value', string='Values')
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')

    @api.model
    def _get_field_types(self):
        return [
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
    def name_to_upper(self):
        if self.field_description:
            self.field_description = str(self.field_description).upper()

    @api.onchange('field_description')
    def _set_name_from_label(self):
        if not self._origin: # Only on create mode
            self.name = 'x_' # Restore original value
            if self.field_description: # If var is False, nothing to do
                slug = unidecode.unidecode(self.field_description).lower() # Change accentuated chars and convert to lowercase
                slug = re.sub(r"[^\w\s]", '', slug) # Remove all non-word characters (everything except numbers and letters)
                slug = re.sub(r"\s+", '_', slug) # Replace all runs of whitespace with a single dash
                self.name = 'x_' + slug # Update field

    @api.onchange('related')
    def _onchange_related(self):
        if self.related:
            try:
                field = self._related_field()
                self.relation = field.comodel_name
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
    def _createFieldsXml(self):
        # import web_pdb; web_pdb.set_trace()
        categorization_product_view = self.env.ref('js_categorization.categorization_product_form_view').sudo()
        categorization_variant_view = self.env.ref('js_categorization.categorization_variant_form_view').sudo()
        categorization_product_search = self.env.ref('js_categorization.categorization_product_search_by_field').sudo()
        categorization_variant_search = self.env.ref('js_categorization.categorization_variant_search_by_field').sudo()
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
        vsea.clear()
        # Create search view xpath attrs, sdoc have a base xpath
        psea.set('expr', "//search")
        psea.set('position', "inside")
        vsea.set('expr', "//search")
        vsea.set('position', "inside")
        # Regenerate fields XML for each type
        categorization_types = [(type.id, type.name) for type in self.env['js_categorization.type'].search([])]
        categorization_types.insert(0, (False, _('Generic')))
        for type in categorization_types:
            # Get fields for this type
            fields_for_type = self.env['js_categorization.field'].search([('categorization_type', '=', type[1])])
            # If have fields
            if len(fields_for_type):
                # Create fields group
                pdoc_field_group = xee.SubElement(pdoc_categorization_section, 'group')
                vdoc_field_group = xee.SubElement(vdoc_categorization_section, 'group')
                if type[1]:
                    pdoc_field_group.set('string', type[1])
                    vdoc_field_group.set('string', type[1])
                # Put condition to hide field if type is selected
                if (type[0] != False):
                    pdoc_field_group.set('attrs', "{ 'invisible': [('categorization_type', '!=', %d)] }" % (type[0]))
                    vdoc_field_group.set('attrs', "{ 'invisible': [('categorization_type', '!=', %d)] }" % (type[0]))
                # Create fields XML
                for field in fields_for_type:
                    if field.model_id.model == 'product.template':
                        doc_field_input = xee.SubElement(pdoc_field_group, 'field')
                    else: # If is a product variant
                        doc_field_input = xee.SubElement(vdoc_field_group, 'field')
                    doc_field_input.set('name', field.name)
                    doc_field_input.set('string', field.field_description)
                    if field.ttype == 'many2many': # If is many2many field
                        doc_field_input.set('widget', 'many2many_tags')
                    if field.ttype in ('many2one', 'many2many'): # If is many2one or many2many field
                        doc_field_input.set('options', "{'no_open': True, 'no_create': True}")
                        doc_field_input.set('domain', "[('id', 'in', %s)]" % (str(field.selection_vals.ids)))
                    if field.index: # If is indexed field
                        if field.model_id.model == 'product.template':
                            doc_field_search = xee.SubElement(psea, 'field')
                        else: # If is a product variant
                            doc_field_search = xee.SubElement(vsea, 'field')
                        doc_field_search.set('name', field.name)
                        doc_field_search.set('string', field.field_description)
        # Save XML to database
        categorization_product_view.arch_base = xee.tostring(pdoc, pretty_print=True)
        categorization_variant_view.arch_base = xee.tostring(vdoc, pretty_print=True)
        categorization_product_search.arch_base = xee.tostring(psea, pretty_print=True)
        categorization_variant_search.arch_base = xee.tostring(vsea, pretty_print=True)

    @api.model
    def _resetXml(self):
        for view in ('categorization_product_search_by_field', 'categorization_variant_search_by_field', 'categorization_product_form_view', 'categorization_variant_form_view'):
            # Get view object
            categorization_view = self.env.ref('js_categorization.' + view).sudo()
            # Get and parse view XML
            doc = xee.fromstring(categorization_view.arch_base)
            # In search view clear all doc and set xpath
            if (view in ('categorization_product_search_by_field', 'categorization_variant_search_by_field')):
                doc.clear()
                doc.set('expr', "//search")
                doc.set('position', "inside")
            else: # On others delete group childs
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
                self._createFieldsXml()
                return result
        except Exception, e:
            # Not make changes in db
            self.env.cr.rollback()
            raise UserError(_('Error creating the field \n%s') % (e))

    @api.multi
    def write(self, values):
        try:
            # If not updating sequence
            if not (values.get('sequence') and len(values) == 1):
                # Write model base field
                self.env['ir.model.fields'].sudo().write(values)
            # Write categorization field
            if super(CategorizationField, self).write(values):
                # Write to database
                self.env.cr.commit()
                # Write fileds to XML
                self._createFieldsXml()
        except Exception, e:
            # Not make changes in db
            self.env.cr.rollback()
            raise UserError(_('Error updating the field \n%s') % (e))

    @api.multi
    def unlink(self):
        try:
            # Reset XML before unlink field
            self._resetXml()
            # Save name to unlink base field
            record_name = self.name
            # Delete categorization field
            if super(CategorizationField, self).unlink():
                # Unlink model base field
                self.env['ir.model.fields'].sudo().search([('name', '=', record_name)]).with_context(_force_unlink=True).unlink()
                # Write to database
                self.env.cr.commit()
                # Write fileds to XML
                self._createFieldsXml()
        except Exception, e:
            # Not make changes in db
            self.env.cr.rollback()
            self._createFieldsXml()
            raise UserError(_('Error deleting the field \n%s') % (e))

class CategorizationValue(models.Model):
    _name = 'js_categorization.value'
    _description = "Categorization Values"
    _sql_constraints = [('categorization_value_unique', 'unique(name)', 'Value must be unique in categorization!')]
    name = fields.Char(required=True, translate=True)

    @api.onchange('name')
    def name_to_lower(self):
        if self.name:
            self.name = str(self.name).lower()
