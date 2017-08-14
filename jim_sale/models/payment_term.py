# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _


class AccountPaymentTerm(models.Model):
    _inherit = "account.payment.term"

    prepayment = fields.Boolean("Advance Payment")