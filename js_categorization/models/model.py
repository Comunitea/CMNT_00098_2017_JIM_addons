# -*- coding: utf-8 -*-
from odoo import api, models
# Change model default order
class IrModel(models.Model):
    _inherit = 'ir.model'
    _order = 'name ASC'
