# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api


class WizDoneCancelPicks(models.TransientModel):
    _name = "wiz.done.cancel.picks"

    wiz_id = fields.Many2one("wiz.return.dest.move.cancelled")
    picking_done_id = fields.Many2one(
        "stock.picking", readonly=1, string="Picking done"
    )
    picking_cancelled_id = fields.Many2one(
        "stock.picking", readonly=1, string="Picking cancelled"
    )
    picking_type_id = fields.Many2one(
        related="picking_done_id.picking_type_id"
    )

    moves = fields.Integer("Moves number")


class WizReturnDestMoveCancelled(models.TransientModel):
    _name = "wiz.return.dest.move.cancelled"

    location_id = fields.Many2one(
        "stock.location",
        string="Location to check",
        help="This is the location dest for done picks\n and location origin for cancelled picks",
    )
    location_dest_id = fields.Many2one(
        "stock.location",
        string="Location dest",
        help="This is the location dest for cancelled picks",
    )
    action_done = fields.Boolean("Auto validation", default=False)
    pick_ids = fields.Many2many(
        "wiz.done.cancel.picks", string="Picking done to canceled", copy=False
    )
    picking_type_id = fields.Many2one("stock.picking.type")
    dst_picking_type_id = fields.Many2one("stock.picking.type")

    @api.model
    def default_get(self, fields):
        res = super(WizReturnDestMoveCancelled, self).default_get(fields)
        res["location_id"] = 69
        res["location_dest_id"] = 33
        res["picking_type_id"] = 95
        res["dst_picking_type_id"] = 4
        return res

    def show_picks(self):
        self.write({"pick_ids": [(5, 0)]})
        sql = self.get_sql_str()
        self.env.cr.execute(sql)
        results = self.env.cr.fetchall()
        if results:
            for result in results:
                self.write({"pick_ids": [(0, 0, self.get_new_line(result))]})
        return {
            "context": self.env.context,
            "view_type": "form",
            "view_mode": "form",
            "res_model": "wiz.return.dest.move.cancelled",
            "res_id": self.id,
            "view_id": False,
            "type": "ir.actions.act_window",
            "target": "new",
        }

    def get_new_line(self, result):
        vals = {
            "wiz_id": self.id,
            "picking_done_id": result[0],
            "picking_cancelled_id": result[1],
            "moves": result[2],
        }

        return vals

    def get_sql_str(self):
        str = (
            "select sp1.id, sp2.id, count(sm1.id) from stock_move sm1 "
            "join stock_move sm2 on sm1.move_dest_id = sm2.id "
            "join stock_picking sp1 on sp1.id = sm1.picking_id "
            "join stock_picking sp2 on sp2.id = sm2.picking_id where "
            "sm2.state = 'cancel' and sm1.state='done' "
            "and sm1.id not in (select origin_returned_move_id from stock_move sm where (sm.origin_returned_move_id = sm1.id)) "
            "and sm1.location_dest_id = sm2.location_id "
        )
        str = str + "and sp1.company_id=%s " % self.env.user.company_id.id
        str = (
            str + "and sm1.location_dest_id=%s " % self.location_id.id
            if self.location_id
            else str
        )
        str = (
            str + "and sm2.location_dest_id=%s " % self.location_dest_id.id
            if self.location_dest_id
            else str
        )
        str = (
            str + "and sp1.picking_type_id=%s " % self.picking_type_id.id
            if self.picking_type_id
            else str
        )
        str = (
            str + "and sp2.picking_type_id=%s " % self.dst_picking_type_id.id
            if self.dst_picking_type_id
            else str
        )
        str = str + "group by sp1.id, sp2.id"

        return str
