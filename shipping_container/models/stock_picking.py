# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    harbor_id = fields.Many2one("res.harbor", string="Harbor")

    @api.model
    def _prepare_picking(self):
        res = super (PurchaseOrder, self)._prepare_picking()
        res['harbor_id'] = self.harbor_id and self.harbor_id.id or False
        return res


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    shipping_container_id = fields.Many2one("shipping.container", "Shipping container",
                                            domain="[('state','in',['draft', 'loading'])]")
    shipping_volume = fields.Float("Volume for Shipping", compute='_compute_shipping_volume')
    harbor_id = fields.Many2one("res.harbor", string="Harbor")


    @api.one
    @api.depends('pack_operation_ids')
    def _compute_shipping_volume(self):
        volume = 0.000
        for packop in self.pack_operation_ids:
            if packop.product_id and not packop.result_package_id:
                volume += packop.product_uom_id._compute_quantity(packop.product_qty,
                                                                  packop.product_id.uom_id) * packop.product_id.volume
        self.shipping_volume = volume

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
