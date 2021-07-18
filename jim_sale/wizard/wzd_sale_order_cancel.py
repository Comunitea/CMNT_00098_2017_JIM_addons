# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _


class WzdSaleOrderCancel(models.TransientModel):

    _name = "wzd.sale.order.cancel"
    _description = "Cancelar Orden de venta"

    def _get_picks(self):
        self.picking_ids = self.sale_id.picking_ids

    sale_id = fields.Many2one("sale.order", "Venta a cancelar")
    state = fields.Selection(related="sale_id.state")
    picking_ids = fields.One2many(
        "stock.picking", string="Picks asociados", compute=_get_picks
    )

    @api.model
    def default_get(self, fields):
        res = super(WzdSaleOrderCancel, self).default_get(fields)
        return res

    def cancel_all(self):
        self.sale_id.action_cancel()
        return {
            "name": "Pedido cancelado",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "sale.order",
            "res_id": self.sale_id.id,
            "context": self.env.context,
        }
