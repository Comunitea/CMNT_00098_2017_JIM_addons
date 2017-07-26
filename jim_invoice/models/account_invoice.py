# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    payment_mode_id = fields.Many2one(
        comodel_name='account.payment.mode', string="Payment Mode",
        ondelete='restrict',
        readonly=True, states={'draft': [('readonly', False)],
                               'open': [('readonly', False)]})