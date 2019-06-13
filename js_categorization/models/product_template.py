# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    categorization_type_id = fields.Many2one('js_categorization.type', string="Type")
    categorization_param_ids = fields.Many2many('js_categorization.param', string="Parameters", domain="[('type_id', '=', categorization_type_id)]")
