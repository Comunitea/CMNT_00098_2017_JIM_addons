# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class AccountPaymentOrder(models.Model):
    _inherit = 'account.payment.order'

    date_uploaded = fields.Date(string='File Upload Date', readonly=True,
                                states={'draft': [('readonly', False)],
                                        'open': [('readonly', False)],
                                        'generated': [('readonly', False)]})

    @api.multi
    def generated2uploaded(self):

        for order in self:
            if order.date_uploaded == False:
                order.date_uploaded = fields.Date.context_today(self)

            if order.payment_mode_id.generate_move:
                order.generate_move()
        self.state = 'uploaded'
        return True

    @api.multi
    def _prepare_move(self, bank_lines=None):
        vals = super(AccountPaymentOrder, self)._prepare_move(bank_lines)
        vals['date']= self.date_uploaded
        return vals