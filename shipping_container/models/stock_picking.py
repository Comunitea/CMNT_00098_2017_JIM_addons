# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class StockPicking(models.Model):

    _inherit = 'stock.picking'

    shipping_container_id = fields.Many2one("shipping.container", "Shipping container",
                                            domain="[('state','in',['draft', 'loading'])]")

    def write(self, vals):
        res = super(StockPicking, self).write(vals)

        shipping_container_id = vals.get('shipping_container_id', False)
        if shipping_container_id:
            shipping_container = self.env['shipping.container'].browse(shipping_container_id)
            if shipping_container.state != 'loading':
                raise ValidationError(_('Container not in "loading" state'))
            for pick in self:
                pick.min_date = shipping_container.date_expected
        return res

class StockMove(models.Model):

    _inherit = 'stock.move'
    shipping_container_id = fields.Many2one(related='picking_id.shipping_container_id')
