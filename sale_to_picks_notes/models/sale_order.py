# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = "sale.order"

    # Char limited to 255 because sga integrated
    invoice_note = fields.Text("Invoice note")
    pick_note = fields.Text("Pick note")
    delivery_note = fields.Text("Delivery note")
    work_to_do = fields.Text("Mrp note")

    @api.multi
    def action_sale(self):
        res = super(SaleOrder, self).action_sale()
        for order in self:
            order.write_notes(["outgoing", "internal", "mrp_operation"])
        return res

    @api.multi
    def write_notes(self, picks):
        def write_note_type(type, field):
            picks = pick_ids.filtered(lambda x: x.picking_type_id.code == type)
            for pick in picks:
                if not pick.note:
                    pick.note = self[field]
                elif not (self[field] in pick.note):
                    pick.note = u"%s\n%s" % (pick.note, self[field])

        pick_ids = self.picking_ids.filtered(lambda x: x.state != "cancel")
        if pick_ids:
            if "outgoing" in picks:
                write_note_type("outgoing", "delivery_note")

            if "internal" in picks:
                write_note_type("internal", "pick_note")

            if "mrp_production" in picks:
                write_note_type("outgoing", "work_to_do")

    @api.multi
    def write_delivery_note(self):
        for order in self:
            order.write_notes("outgoing")

    @api.multi
    def write_pick_note(self):
        for order in self:
            order.write_notes("internal")

    @api.multi
    def write_work_to_do(self):
        for order in self:
            order.write_notes("mrp_operation")

    @api.multi
    def write_invoice_note(self):
        return
