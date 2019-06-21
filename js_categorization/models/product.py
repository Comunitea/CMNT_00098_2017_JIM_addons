# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    def _get_type_default(self):
        return self.env.ref('js_categorization.generic_type').id

    categorization_type = fields.Many2one('js_categorization.type', string="Cat. Type", default=_get_type_default, required=True)

    @api.multi
    def edit_unique_variant(self):
    	return {
            'name': 'Product Variant',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.product',
            'res_id': self.product_variant_id.id,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def new_field_modal(self):
    	return {
            'name': 'Categrization Field',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'js_categorization.field',
            'context': { 'default_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id },
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def edit_product(self):
    	return {
            'name': 'Product Template',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.template',
            'res_id': self.product_tmpl_id.id,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def new_field_modal(self):
    	return {
            'name': 'Categorization Field',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'js_categorization.field',
            'context': { 'default_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id },
            'type': 'ir.actions.act_window',
            'target': 'new'
        }
