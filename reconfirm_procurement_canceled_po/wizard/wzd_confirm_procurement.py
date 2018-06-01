# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class WzdConfirmProcurement(models.TransientModel):
    _name = 'wzd.confirm.procurement'
    _description = 'Confirm procurement in canceled purchases'

    purchase_ids = fields.Many2many('purchase.order')
    procurement_ids = fields.Many2many('procurement.order')


    @api.model
    def default_get(self, fields):
        res = super(WzdConfirmProcurement, self).default_get(fields)
        return res

    @api.multi
    def reconfirm_procurement(self):
        ctx = self._context.copy()
        ctx.update(force_procurement=True)
        self.purchase_ids.with_context(ctx).button_confirm()

    @api.multi
    def not_reconfirm_procurement(self):
        ctx = self._context.copy()
        ctx.update(force_procurement=False)
        self.purchase_ids.with_context(ctx).button_confirm()