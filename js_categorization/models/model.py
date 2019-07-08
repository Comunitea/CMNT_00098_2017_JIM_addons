# -*- coding: utf-8 -*-
from odoo import api, models

class IrModel(models.Model):
    _inherit = 'ir.model'

    @api.multi
    def name_get(self):
        data = super(IrModel, self).name_get()
        data.sort(key=lambda tup: tup[1])
        return data
