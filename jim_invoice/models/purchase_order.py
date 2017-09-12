# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _

class PurchaseOrder(models.Model):
    _inherit = "purchase.order"

    force_invoiced_status = fields.Boolean("Marcar como facturado")

    @api.depends('state', 'order_line.qty_invoiced', 'order_line.qty_received', 'order_line.product_qty','force_invoiced_status')
    def _get_invoiced(self):
        res = super(PurchaseOrder, self)._get_invoiced()
        for order in self:
            if order.state in ('purchase', 'done') and order.force_invoiced_status:
                order.update({'invoice_status': 'invoiced'})
        return res