# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, api


class SaleOrder(models.Model):

    _inherit = "sale.order"

    do_backorder = fields.Selection(
        [("default", "Por defecto"), ("yes", "Si"), ("no", "No")],
        "Entrega parcial",
        default="no",
    )

    @api.multi
    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            order.onchange_do_backorder()
        return res

    @api.onchange("do_backorder")
    def onchange_do_backorder(self):

        self.picking_ids.sudo().filtered(
            lambda x: x.picking_type_id.sga_integrated
        ).write({"do_backorder": self.do_backorder})

        # for pick in self.picking_ids.sudo().filtered(lambda x: x.picking_type_id.sga_integrated):
        #    pick.write({'do_backorder': self.do_backorder})
