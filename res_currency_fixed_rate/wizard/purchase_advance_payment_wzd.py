# © 2016 Comunitea - Kiko Sanchez <kiko@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).


from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp


class AccountVoucherWizard(models.TransientModel):

    _inherit = "account.purchase.voucher.wizard"

    def make_advance_payment(self):
        # No quiero post
        ctx = dict(self._context.copy())
        ctx.update({"no_post": True})
        res = super(
            AccountVoucherWizard, self.with_context(ctx)
        ).make_advance_payment()
        return res

    def get_payment_res(self, purchase_ids):
        payment_res = super(AccountVoucherWizard, self).get_payment_res(
            purchase_ids
        )
        purchase_obj = self.env["purchase.order"]
        purchase_id = purchase_ids[0]
        purchase = purchase_obj.browse(purchase_id)
        payment_res["fixed_rate"] = self.purchase_exchange_rate
        payment_res["rate"] = self.exchange_rate
        return payment_res

    purchase_exchange_rate = fields.Float(
        "Purchase exchange rate", digits=(16, 6)
    )
    purchase_id = fields.Many2one("purchase.order")

    @api.model
    def default_get(self, fields):
        res = super(AccountVoucherWizard, self).default_get(fields)
        purchase_ids = self.env.context.get("active_ids", [])
        if not purchase_ids:
            return res
        purchase_id = purchase_ids[0]
        purchase = self.env["purchase.order"].browse(purchase_id)
        res.update(
            {
                "purchase_id": purchase_id,
                "purchase_exchange_rate": purchase.order_exchange_rate,
            }
        )
        return res

    @api.onchange("amount_advance")
    def onchange_amount(self):
        super(AccountVoucherWizard, self).onchange_amount()
        exchange_rate = self.purchase_exchange_rate or self.exchange_rate
        self.currency_amount = self.amount_advance * (1.0 / exchange_rate)

    @api.onchange("purchase_exchange_rate")
    def onchange_purchase_exchange_rate(self):
        exchange_rate = self.purchase_exchange_rate or self.exchange_rate
        self.currency_amount = self.amount_advance * (1.0 / exchange_rate)
