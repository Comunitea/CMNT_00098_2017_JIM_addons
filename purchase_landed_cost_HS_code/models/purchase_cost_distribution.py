# -*- coding: utf-8 -*-
# © 2018 Santi Argüeso <santi@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3


from odoo import models, fields, exceptions, api, _
import odoo.addons.decimal_precision as dp


class PurchaseCostDistributionLine(models.Model):
    _inherit = 'purchase.cost.distribution.line'

    tax = fields.Float(
        string='Tax (%)', digits=dp.get_precision('Account'))

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        for line in self:
            self.tax = line.product_id.hs_code_id.country_tax_ids.filtered(
                lambda x: x.country_id.id ==
                          x.partner.country_id.id).tax or 0
