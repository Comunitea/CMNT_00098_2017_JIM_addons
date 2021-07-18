# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    def get_rate(self):
        self.order_exchange_rate = 0
        if self.company_id.currency_id and self.currency_id:
            self.order_exchange_rate = (
                self.env["res.currency"]
                .with_context(date=self.date_order)
                ._get_conversion_rate(
                    self.company_id.currency_id, self.currency_id
                )
            )

    order_exchange_rate = fields.Float(
        "Exchange rate", digits=(16, 6), default=get_rate
    )
    hide_exc = fields.Boolean(string="Hide", compute="onchange_hide_exc")

    @api.depends("currency_id", "company_id", "partner_id")
    def onchange_hide_exc(self):
        if not self.currency_id or (
            self.currency_id == self.company_id.currency_id
        ):
            self.hide_exc = False
        else:
            self.hide_exc = True

    @api.onchange("partner_id", "company_id")
    def onchange_partner_id(self):
        super(PurchaseOrder, self).onchange_partner_id()
        self.get_rate()

    @api.onchange("currency_id")
    def onchange_currency_id(self):
        self.get_rate()
