# -*- coding: utf-8 -*-
# © 2017 Techspawn Solutions
# © 2015 Eezee-It, MONK Software, Vauxoo
# © 2013 Camptocamp
# © 2009-2013 Akretion,
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class AccountInvoice(models.Model):

    _inherit = "account.invoice"

    def _get_claim_ids(self):
        for invoice in self:
            invoice.claim_ids = self.env['crm.claim'].search([('invoice_id', '=', self.id)])

    claim_ids = fields.One2many('crm.claim', string='Claims RMA', compute=_get_claim_ids)
