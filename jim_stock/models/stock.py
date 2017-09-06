# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp

class StockPicking (models.Model):
    _inherit = "stock.picking"
    pick_weight = fields.Float(string='Shipping Weight',
                 help="Manual weight in pick. Propagate to next asociated pick.")
    partner_id = fields.Many2one(
        'res.partner', 'Partner', required=1, default=lambda self: self.env.user.company_id.partner_id.id,
        states={})

    observations = fields.Text(related='sale_id.observations')
    purchase_date_order = fields.Datetime(related="purchase_id.date_order")
    confirmation_date = fields.Datetime(related="sale_id.confirmation_date")

class StockLocation(models.Model):
    _inherit = "stock.location"

    deposit = fields.Boolean('Deposit')


class StockQuantPackage(models.Model):

    _inherit = "stock.quant.package"

    @api.depends('quant_ids', 'children_ids')
    def _compute_volume(self):
        volume = 0
        for quant in self.quant_ids:
            volume += quant.qty * quant.product_id.volume
        for pack in self.children_ids:
            pack._compute_volume()
            volume += pack.volume
        self.volume = volume

    @api.depends('height', 'width', 'length', 'volume')
    def _compute_package_volume(self):

        self.shipping_volume = (self.width * self.height * self.length) or self.volume

    packaging_id_code = fields.Char(related='packaging_id.shipper_package_code')
    height = fields.Float('Height')
    width = fields.Float('Width')
    length = fields.Float('Length')
    volume = fields.Float(compute='_compute_volume', digits=(10, 6))
    shipping_volume = fields.Float(string='Shipping Volume',
                                   compute="_compute_package_volume",
                                   digits=(10, 6))
