# Copyright 2015 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
import odoo.addons.decimal_precision as dp


class AccountVoucherWizard(models.TransientModel):

    _inherit = "account.purchase.voucher.wizard"

    def make_advance_payment(self):
        """Create customer paylines and validates the payment"""
        ## Neceito dividir para heredar y añadir campos, así como poder evirar llamar a do_post si viene a True en context

        # res = super(AccountVoucherWizard, self).make_advance_payment()

        no_post = self._context.get("no_post", False)
        payment_obj = self.env["account.payment"]
        purchase_ids = self.env.context.get("active_ids", [])
        if purchase_ids:
            payment_res = self.get_payment_res(purchase_ids)
            payment = payment_obj.create(payment_res)
            if not no_post:
                payment.post()
            else:
                payment.create_forecast_entry()
        return {
            "type": "ir.actions.act_window_close",
        }
