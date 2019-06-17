# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
import xml.etree.ElementTree as xee
from odoo.exceptions import UserError

class CategorizationType(models.Model):
    _name = 'js_categorization.type'
    _description = "Categorization types"
    _sql_constraints = [('categorization_type_unique', 'unique(name)', 'Type must be unique in categorization!')]
    name = fields.Char(required=True, translate=False)

class CategorizationField(models.Model):
    _name = 'js_categorization.field'
    _description = 'Categorization fields'
    _inherit = 'ir.model.fields'

    @api.multi
    def _set_mod_default(self):
        model_ids = self.env['ir.model'].sudo().search([('model', 'in', ['product.template',  'product.product'])])
        return [('id', 'in', model_ids.ids)]

    name = fields.Char(copy=False)
    sequence = fields.Integer(help="Determine the display order", default=10)
    categorization_type = fields.Many2one('js_categorization.type', ondelete='restrict', string='Cat. Type', required=False)
    model_id = fields.Many2one(domain=_set_mod_default)
    ref_model_id = fields.Many2one('ir.model', string='Model', index=True)
    rel_field = fields.Many2one('ir.model.fields', string='Related Field')

    @api.model
    def _get_field_types(self):
        field_list = sorted((key, key) for key in fields.MetaField.by_type)
        field_list.remove(('one2many', 'one2many'))
        field_list.remove(('reference', 'reference'))
        field_list.remove(('serialized', 'serialized'))
        return field_list

    @api.model
    def _createFieldXml(self, vals):
        # Get vals, if updating vals only contains modified fields
        model_id = vals.get('model_id') if vals.get('model_id') else vals.get('model_id', self.model_id.id)
        name = vals.get('name') if vals.get('name') else vals.get('name', self.name)
        label = vals.get('field_description') if vals.get('field_description') else vals.get('field_description', self.field_description)
        position_field = vals.get('position_field') if vals.get('position_field') else vals.get('position_field', self.position_field.id)
        position = vals.get('position') if vals.get('position') else vals.get('position', self.position)
        ctype = vals.get('categorization_type') if vals.get('categorization_type') else vals.get('categorization_type', self.categorization_type.id)
        # Search others vals from model
        inherit_id = self.env.ref('js_categorization.categorization_product_template_form_view').id
        linked_model = self.env['ir.model'].sudo().browse(model_id).model
        pos_field_name = self.env['ir.model.fields'].sudo().browse(position_field).name
        # Create field XML
        return self.env['ir.ui.view'].sudo().create({
            'name': 'js_categorization.' + name,
            'type': 'form',
            'model': linked_model,
            'mode': 'extension',
            'inherit_id': inherit_id,
            'arch_base': (
                '<?xml version="1.0"?>'
                '<data>'
                        '<group>'
                            '<label for="' + str(name) + '" string="' + str(label) + '"/>'
                            '<div>'
                                '<field name="' + str(name) + '" attrs="{ \'invisible\': [(\'categorization_type.id\', \'!=\', ' + str(ctype) + ')] and not ' + str(ctype) + ' }"/>'
                            '</div>'
                        '</group>'
                '</data>'
            ),
            'active': True
        })

    @api.model
    def create(self, values):
        self.env['ir.model.fields'].sudo().create(values)
        self._createFieldXml(values)
        return super(CategorizationField, self).create(values)

    @api.one
    def write(self, values):
        for record in self:
            #import web_pdb; web_pdb.set_trace()
            self.env['ir.ui.view'].sudo().search([('name','=','js_categorization.' + record.name)]).unlink()
            record.env['ir.model.fields'].sudo().write(values)
            record._createFieldXml(values)
            super(CategorizationField, record).write(values)

    @api.multi
    def unlink(self):
        for record in self:
            record_name = record.name
            self.env['ir.ui.view'].sudo().search([('name','=','js_categorization.' + record_name)]).unlink()
            super(CategorizationField, record).unlink()
            self.env['ir.model.fields'].sudo().search([('name','=',record_name)]).with_context(_force_unlink=True).unlink()

class CategorizationValue(models.Model):
    _name = 'js_categorization.value'
    _description = "Categorization values"
    name = fields.Char(required=True, translate=True)
