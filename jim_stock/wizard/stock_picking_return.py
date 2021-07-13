# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError

DOMAIN_LOCATION_ID = "['|', ('id', '=', original_location_id), '&', ('return_location', '=', True), ('id', 'child_of', parent_location_id)]"


class StockPicking(models.Model):
    _inherit = "stock.picking"

    @api.multi
    def copy(self, default=None):

        if self._context.get("return_picking", False) and self._context.get(
            "picking_type_id", False
        ):
            default.update(
                {"picking_type_id": self._context["picking_type_id"]}
            )
        return super(StockPicking, self).copy(default)


class StockMove(models.Model):

    _inherit = "stock.move"

    returned_qty = fields.Float(
        "Returned quantity", digits=dp.get_precision("Product Unit of Measure")
    )

    @api.multi
    def copy(self, default=None):
        if self._context.get("return_picking", False) and self._context.get(
            "picking_type_id", False
        ):
            default.update(
                {"picking_type_id": self._context["picking_type_id"]}
            )
        return super(StockMove, self).copy(default)


class StockReturnPickingLine(models.TransientModel):
    _inherit = "stock.return.picking.line"

    qty_done = fields.Float(
        "Quantity done", digits=dp.get_precision("Product Unit of Measure")
    )
    ordered_qty = fields.Float(
        "Ordered quantity", digits=dp.get_precision("Product Unit of Measure")
    )
    quantity = fields.Float(
        "Quantity available",
        digits=dp.get_precision("Product Unit of Measure"),
        required=True,
    )
    description = fields.Char("Producto")


class StockReturnPicking(models.TransientModel):
    _inherit = "stock.return.picking"

    location_id = fields.Many2one("stock.location", "Return Location")
    # domain="['|', ('id', '=', original_location_id), '&', ('return_location', '=', True), ('id', 'child_of', parent_location_id)]")

    only_return_location = fields.Boolean("Only return location")
    picking_type_id = fields.Many2one(
        "stock.picking.type",
        "Picking Type",
    )
    picking_id = fields.Many2one("stock.picking")
    to_refund_all = fields.Boolean("To refund")

    @api.model
    def default_get(self, fields):
        res = super(StockReturnPicking, self).default_get(fields)
        if res and "product_return_moves" in res:
            new_product_return_moves = []
            product_return_moves = res["product_return_moves"]
            Quant = self.env["stock.quant"]
            picking = self.env["stock.picking"].browse(
                self.env.context.get("active_id")
            )
            if picking:
                to_refund_all = self._context.get("to_refund_all", True)

                res.update(
                    {
                        "picking_type_id": picking.picking_type_id.return_picking_type_id.id
                        or picking.picking_type_id.id,
                        "picking_id": picking.id,
                        "to_refund_all": to_refund_all,
                    }
                )
                for return_move in product_return_moves:
                    new_move = return_move[2]
                    orig_move = picking.move_lines.filtered(
                        lambda x: x.id == new_move["move_id"]
                    )
                    quantity = sum(
                        quant.qty
                        for quant in Quant.search(
                            [
                                ("history_ids", "in", orig_move.id),
                                ("qty", ">", 0.0),
                                (
                                    "location_id",
                                    "child_of",
                                    orig_move.location_id.id,
                                ),
                            ]
                        ).filtered(
                            lambda quant: not quant.reservation_id
                            or quant.reservation_id.origin_returned_move_id
                            != orig_move
                        )
                    )
                    quantity = (
                        orig_move.product_uom_qty
                    )  # - orig_move.product_id.uom_id._compute_quantity(quantity, orig_move.product_uom)
                    new_move.update(
                        {
                            "qty_done": quantity,
                            "to_refund_so": to_refund_all,
                            "description": orig_move.product_id.display_name,
                        }
                    )
                    new_product_return_moves.append((0, 0, new_move))
                res.update({"product_return_moves": new_product_return_moves})
        return res

    @api.onchange("picking_type_id")
    def onchange_picking_type_id(self):
        self.only_return_location = False
        self.location_id = self.picking_type_id.default_location_dest_id

    @api.onchange("only_return_location")
    def onchange_only_return_location(self):

        if self.only_return_location:
            domain = [
                "|",
                ("id", "=", self.original_location_id.id),
                "&",
                ("return_location", "=", True),
                ("id", "child_of", self.parent_location_id.id),
            ]
        else:
            domain = []
        return {"domain": {"location_id": domain}}

    @api.multi
    def _create_returns(self):
        # TDE FIXME: store it in the wizard, stupid
        # Sobre escribo todo para coger valores del formulario
        picking = self.env["stock.picking"].browse(
            self.env.context["active_id"]
        )
        ctx = self._context.copy()
        ctx.update(
            {
                "return_picking": True,
                "picking_type_id": self.picking_type_id.id,
            }
        )
        self = self.with_context(ctx)
        id, picking_type_id = super(StockReturnPicking, self)._create_returns()
        new_moves = self.env["stock.move"].search([("picking_id", "=", id)])
        for new_move in new_moves:
            new_move.purchase_line_id = (
                new_move.origin_returned_move_id.purchase_line_id
            )
        for return_line in self.product_return_moves:
            return_line.move_id.returned_qty += return_line.quantity
            new_move.origin_returned_move_id.returned_qty += (
                new_move.product_uom_qty
            )
        self.env["stock.picking"].browse(id).write(
            {"returned_picking_id": self.env.context["active_id"]}
        )
        return id, picking_type_id

    def create_returns_from_qty_done(self):
        for move in self.product_return_moves:
            move.quantity = move.qty_done
        return self.create_returns()

    def create_returns_from_ordered_qty(self):
        for move in self.product_return_moves:
            move.quantity = move.ordered_qty
        return self.create_returns()

    def set_to_true_refund(self):
        return self.set_to_refund(True)

    def set_to_false_refund(self):
        return self.set_to_refund(False)

    def set_to_refund(self, option=False):
        self.to_refund_all = option
        ctx = self._context.copy()
        ctx.update(to_refund_all=self.to_refund_all)
        action = {
            "name": "Reverse Transfer",
            "type": "ir.actions.act_window",
            "id": "act_stock_return_picking",
            "res_model": "stock.return.picking",
            "view_mode": "form",
            "target": "new",
            "context": ctx,
        }
        return action
