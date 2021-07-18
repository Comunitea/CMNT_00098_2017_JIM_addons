# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, api, tools


class StockPicking(models.Model):

    _inherit = "stock.picking"

    hide_next_canceled = fields.Boolean(
        "Reviewed (done to cancel)",
        help="Show in done to cancel picks",
        default=False,
    )


class UtilsDoneCancelPicks(models.Model):

    _name = "done.to.cancel.picks"
    _description = "Done pick to cancelled pick"
    _auto = False
    _rec_name = "picking_done_id"
    _order = "picking_done_id"

    picking_done_id = fields.Many2one(
        "stock.picking", readonly=1, string="Picking done"
    )
    picking_cancelled_id = fields.Many2one(
        "stock.picking", readonly=1, string="Picking cancelled"
    )
    picking_type_id = fields.Many2one("stock.picking.type")
    partner_id = fields.Many2one("res.partner", string="Customer/Supplier")
    sale_id = fields.Many2one(related="picking_cancelled_id.orig_sale_id")
    purchase_id = fields.Many2one(related="picking_cancelled_id.purchase_id")
    moves = fields.Integer("Moves number")
    company_id = fields.Many2one("res.company", string="Company")
    orig_loc_id = fields.Many2one("stock.location", "Orig location")
    act_loc_id = fields.Many2one("stock.location", "Actual location")
    next_loc_id = fields.Many2one("stock.location", "Actual location")

    def _select(self):
        select_str = """
        select
        sp1.id as id,
        sp1.id as picking_done_id,
        sp2.id as picking_cancelled_id,
        sp2.picking_type_id as picking_type_id,
        sp2.partner_id as partner_id,
        count(sm1.id) as moves,
        sp2.company_id as company_id,
        sp1.location_id as orig_loc_id,
        sp1.location_dest_id as act_loc_id,
        sp2.location_dest_id as next_loc_id
        """

        return select_str

    def _from(self):
        from_str = """
        stock_move sm1
        join stock_move sm2 on sm1.move_dest_id = sm2.id
        join stock_picking sp1 on sp1.id = sm1.picking_id
        join stock_picking sp2 on sp2.id = sm2.picking_id
        where sm2.state = 'cancel' and sm1.state='done' and not sp1.hide_next_canceled
        and sm1.location_dest_id = sm2.location_id
        group by sp1.id, sp2.id, sp2.picking_type_id, sp2.company_id, sp1.location_id, sp1.location_dest_id, sp2.location_dest_id, sp2.partner_id
        order by sp1.id
        """
        return from_str

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        sql = """CREATE or REPLACE VIEW %s as (%s FROM %s)""" % (
            self._table,
            self._select(),
            self._from(),
        )
        self.env.cr.execute(sql)

    def set_hide_done_to_cancel(self):
        pick_ids = self.mapped("picking_done_id").ids
        return (
            self.env["stock.picking"]
            .browse(pick_ids)
            .write({"hide_next_canceled": True})
        )
