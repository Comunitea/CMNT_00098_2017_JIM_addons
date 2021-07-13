# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models
from odoo import api, models


class StockMove(models.Model):

    _inherit = "stock.move"

    claim_line_id = fields.Many2one("claim.line", copy=True)


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.depends("move_lines")
    def get_returned_picking(self):
        for pick in self:
            move = pick.move_lines.filtered(
                lambda x: x.origin_returned_move_id != False
            )
            pick.returned_picking = (
                move and move[0].origin_returned_move_id.picking_id or False
            )
            # if any(move.to_refund_so for move in self.move_lines):
            #     pick.returned_picking = True

    # returned_picking = fields.Many2one('stock.picking', compute="get_returned_picking")

    def print_this_pick(self):
        return self.env["report"].get_action(
            self, "sga_file.report_picking_mar"
        )

    def open_this_pick(self):
        res = {
            "type": "ir.actions.act_window",
            "name": ("Albarán"),
            "view_mode": "form, tree",
            "view_type": "form",
            "res_model": "stock.picking",
            "res_id": self.id,
        }
        return res

    @api.multi
    def unlink(self):
        claim_ids = self.env["crm.claim"]
        for pick in self:
            if pick.claim_id:
                claim_ids |= pick.claim_id

        res = super(StockPicking, self).unlink()
        if claim_ids:
            claim_ids._get_picked()
        return res
