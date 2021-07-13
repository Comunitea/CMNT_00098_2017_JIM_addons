# © 2016 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    scheduled_order = fields.Boolean("Scheduled Order")
    confirmation_date = fields.Datetime(related="sale_id.confirmation_date")

    def show_packs_in_pick(self):
        ids = []
        for op in self.pack_operation_ids:
            ids.append(op.id)
        view_id = self.env["ir.model.data"].xmlid_to_res_id(
            "jim_sale.stock_pack_picks_tree"
        )
        # view_id = self.env.ref('stock_pack_picks_tree').id
        return {
            "domain": "[('id','in', " + str(ids) + ")]",
            "name": _("Packing List"),
            "view_type": "form",
            "view_mode": "tree",
            "res_model": "stock.pack.operation",
            "view_id": view_id,
            "context": False,
            "type": "ir.actions.act_window",
        }

    @api.multi
    def do_transfer(self):
        return super(StockPicking, self).do_transfer()

    def _add_delivery_cost_to_so(self):
        # Eliminamos la funcioanalidad de ñadir el producto al pedido
        pass
        # self.ensure_one()
        # sale_order = self.sale_id
        # if sale_order.invoice_shipping_on_delivery:
        #     sale_order._create_delivery_line(self.carrier_id, self.carrier_price)

    def product_qty_to_qty_done(self):
        if self.state in ("assigned", "partially_available"):
            if all(x.qty_done == 0 for x in self.pack_operation_product_ids):
                for pack in self.pack_operation_ids:
                    if pack.product_qty > 0:
                        pack.write({"qty_done": pack.product_qty})
                    else:
                        pack.unlink()

    @api.multi
    def write(self, vals):
        if "partner_id" in vals:
            for order in self.filtered(lambda x: x.partner_id):
                message = (
                    "Se ha modificado la empresa <a href=# data-oe-model=res.partner data-oe-id=%d>%s</a>"
                    % (order.partner_id.id, order.partner_id.name)
                )
                order.message_post(body=message)

        return super(StockPicking, self).write(vals)
