# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    categorization_type = fields.Many2one('js_categorization.type', string="Type", required=False)

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
