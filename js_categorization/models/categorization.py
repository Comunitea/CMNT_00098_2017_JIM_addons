# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import AccessError, UserError
#import xml.etree.ElementTree as xee
import lxml.etree as xee
import unidecode
import re

class CategorizationType(models.Model):
    _name = 'js_categorization.type'
    _description = "Categorization types"
    _sql_constraints = [('categorization_type_unique', 'unique(name)', 'Type must be unique in categorization!')]
    _order = 'sequence, name, id'
    name = fields.Char(required=True, translate=False)
    sequence = fields.Integer(help="Determine the display order", default=10)

    @api.model
    def _check_restrictions(self):
        if self.id == self.env.ref('js_categorization.generic_type').id:
            raise AccessError(_('Can not update/delete %s type because is managed by the module!') % (self.name))

    @api.multi
    def write(self, values):
        for record in self:
            # Only update sequence in module types
            if len(values) > 1 or not values.get('sequence'):
                record._check_restrictions()
        return super(CategorizationType, self).write(values)

    @api.multi
    def unlink(self):
        for record in self:
            record._check_restrictions()
            super(CategorizationType, record).unlink()

class CategorizationField(models.Model):
    _name = 'js_categorization.field'
    _description = 'Categorization fields'
    _inherit = 'ir.model.fields'
    _order = 'sequence, field_description, id'

    def _set_mod_default(self):
        model_ids = self.env['ir.model'].sudo().search([('model', 'in', ['product.template',  'product.product'])])
        return [('id', 'in', model_ids.ids)]

    def _get_type_default(self):
        return self.env.ref('js_categorization.generic_type').id

    name = fields.Char(copy=False)
    sequence = fields.Integer(help="Determine the display order", default=100)
    categorization_type = fields.Many2one('js_categorization.type', ondelete='restrict', string='Cat. Type', default=_get_type_default, required=True)
    model_id = fields.Many2one(domain=_set_mod_default)
    selection_vals = fields.Many2many('js_categorization.value', string='Values')
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')

    @api.model
    def _get_field_types(self):
        return [
            ('char', 'Texto'),
            ('date', 'Fecha'),
            ('float', 'Decimal'),
            ('monetary', 'Moneda'),
            ('integer', 'Entero'),
            ('many2one', 'Selección'), # Special selection for categorization values
            ('many2many', 'Multi-selección'), # Special multi-selection for categorization values
            ('text', 'Texto largo')
        ]

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
            except UserError as e:
                return { 'warning': { 'title': _("Warning"), 'message': _("Relation not valid on selected model!") }}
            self.relation = field.comodel_name
            self.readonly = True
            self.store = False
            self.copy = False

    @api.model
    def _createFieldsXml(self):
        categorization_generic_type = self.env.ref('js_categorization.generic_type')
        categorization_product_view = self.env.ref('js_categorization.categorization_product_form_view').sudo()
        categorization_variant_view = self.env.ref('js_categorization.categorization_variant_form_view').sudo()
        # Parse XML string
        parser = xee.XMLParser(remove_blank_text=True)
        pdoc = xee.fromstring(categorization_product_view.arch_base, parser=parser)
        vdoc = xee.fromstring(categorization_variant_view.arch_base, parser=parser)
        # Get fields container
        pdoc_categorization_section = pdoc.find('.//div[@id="categorization_fields"]/group')
        vdoc_categorization_section = vdoc.find('.//div[@id="categorization_fields"]/group')
        # Remove all sub-elements (childs)
        pdoc_categorization_section.clear()
        vdoc_categorization_section.clear()
        # Regenerate fields XML for each type
        for type in self.env['js_categorization.type'].search([]):
            # Get fields for this type
            fields_for_type = self.env['js_categorization.field'].search([('categorization_type', '=', type.name)])
            # If have fields
            if len(fields_for_type):
                # Create fields group
                pdoc_field_group = xee.SubElement(pdoc_categorization_section, 'group')
                vdoc_field_group = xee.SubElement(vdoc_categorization_section, 'group')
                pdoc_field_group.set('string', type.name)
                vdoc_field_group.set('string', type.name)
                # Put condition to hide field if other type is selected (generic excluded)
                if (type.id != categorization_generic_type.id):
                    pdoc_field_group.set('attrs', "{ 'invisible': [('categorization_type', '!=', %d)] }" % (type.id))
                    vdoc_field_group.set('attrs', "{ 'invisible': [('categorization_type', '!=', %d)] }" % (type.id))
                # Create fields XML
                for field in fields_for_type:
                    if field.model_id.model == 'product.template':
                        doc_field_input = xee.SubElement(pdoc_field_group, 'field')
                    else:
                        doc_field_input = xee.SubElement(vdoc_field_group, 'field')
                    doc_field_input.set('name', field.name)
                    doc_field_input.set('string', field.field_description)
                    if field.ttype == 'many2many':
                        doc_field_input.set('widget', 'many2many_tags')
                    if field.ttype in ('many2one', 'many2many'):
                        doc_field_input.set('options', "{'no_open': True, 'no_create': True}")
                        doc_field_input.set('domain', "[('id', 'in', %s)]" % (str(field.selection_vals.ids)))
        # Save XML to database
        # import web_pdb; web_pdb.set_trace()
        categorization_product_view.arch_base = xee.tostring(pdoc, pretty_print=True)
        categorization_variant_view.arch_base = xee.tostring(vdoc, pretty_print=True)

    @api.model
    def _resetXml(self):
        for view in ('js_categorization.categorization_product_form_view', 'js_categorization.categorization_variant_form_view'):
            # Get view object
            categorization_view = self.env.ref(view).sudo()
            # Get and parse view XML
            doc = xee.fromstring(categorization_view.arch_base)
            # Delete all childs
            doc_cat_section = doc.find('.//div[@id="categorization_fields"]/group').clear()
            # Save to field
            categorization_view.arch_base = xee.tostring(doc)

    @api.model
    def _checkFieldRestrictions(self, vals):
        # This restrictions are copied from base module, file ir.model.py, method create()
        # It is necessary to check this before do nothing
        if vals.get('state', 'manual') == 'manual':
            if vals.get('relation') and not self.env['ir.model'].search([('model', '=', vals['relation'])]):
                raise UserError(_("Model %s does not exist!") % vals['relation'])
            if vals.get('ttype') == 'one2many':
                if not self.search([('model_id', '=', vals['relation']), ('name', '=', vals['relation_field']), ('ttype', '=', 'many2one')]):
                    raise UserError(_("Many2one %s on model %s does not exist!") % (vals['relation_field'], vals['relation']))

    @api.model
    def create(self, values):
        try:
            # If is relational field set relation to js_categorization.value
            if values.get('ttype') in ('many2one', 'many2many'):
                values.update({'relation': 'js_categorization.value'})
            # Check restrictions before create
            self._checkFieldRestrictions(values)
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
        except:
            # Not make changes in db
            self.env.cr.rollback()
            return False

    @api.multi
    def write(self, values):
        try:
            # If not updating sequence
            if not (values.get('sequence') and len(values) == 1):
                # Check restrictions before write
                self._checkFieldRestrictions(values)
                # Write model base field
                self.env['ir.model.fields'].sudo().write(values)
            # Write categorization field
            if super(CategorizationField, self).write(values):
                # Write to database
                self.env.cr.commit()
                # Write fileds to XML
                self._createFieldsXml()
        except:
            # Not make changes in db
            self.env.cr.rollback()

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
        except:
            # Not make changes in db
            self.env.cr.rollback()

class CategorizationValue(models.Model):
    _name = 'js_categorization.value'
    _description = "Categorization values"
    name = fields.Char(required=True, translate=True)
