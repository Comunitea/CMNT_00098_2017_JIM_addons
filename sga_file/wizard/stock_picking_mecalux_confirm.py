# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class StockMecaluxConfirm(models.TransientModel):
    _name = "stock.mecalux.confirm"
    _description = "Confirmación de Mecalux"

    pick_id = fields.Many2one("stock.picking", "Pick a enviar")
    state = fields.Selection(related="pick_id.state", readonly=1)

    action_done_bool = fields.Boolean(related="pick_id.action_done_bool")
    do_backorder = fields.Selection(related="pick_id.do_backorder")

    # ~ @api.model
    # ~ def default_get(self, fields):

    # ~ return super(StockMecaluxConfirm, self).default_get(fields)
    # ~ if not res["pick_id"]:
    # ~ res["pick_id"] = self._context.get("active_id", False)
    # ~ return res

    @api.multi
    def process_force_and_send(self):
        self.ensure_one()
        self.pick_id.message_post(
            body=u"Env a Mecalux<em>%s</em> <b>Forzado y envío </b>."
            % self.pick_id.name
        )

        if self.state == "confirmed":
            self.pick_id.force_assign()

        if self.state == "partially_available":
            self.pick_id.force_assign()

        if self.state == "assigned":
            self.pick_id.new_mecalux_file()

    @api.one
    def process_send(self):
        self.ensure_one()
        self.pick_id.message_post(
            body=u"Envío a Mecalux<em>%s</em> <b>Envío</b>."
            % self.pick_id.name
        )
        self.pick_id.new_mecalux_file(force=True)

    @api.one
    def process_force(self):
        self.ensure_one()
        self.pick_id.message_post(
            body=u"Envío a Mecalux<em>%s</em> <b>Forzado</b>."
            % self.pick_id.name
        )
        self.pick_id.force_assign()
