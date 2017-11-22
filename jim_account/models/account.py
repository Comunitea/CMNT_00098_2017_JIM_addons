# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models


class AccountMoveLine(models.Model):

    _inherit = 'account.move.line'

    @api.multi
    def get_mandate_scheme(self):
        for line in self:
            if line.mandate_id:
                line.scheme = line.mandate_id.scheme

    @api.model
    def _mandate_scheme_search(self, operator, operand):

        moves = self.search([('mandate_id.scheme', operator,
                              operand)])
        return [('id', 'in', moves.mapped('id'))]

    scheme = fields.Selection(selection=[('CORE', 'Basic (CORE)'),
                                         ('B2B', 'Enterprise (B2B)')],
                              string='Scheme',
                              compute='get_mandate_scheme',
                              search='_mandate_scheme_search')
    payment_order_line_ids = fields.One2many(
        'account.payment.line', 'move_line_id', string='Payment Line',
        readonly=True)


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    user_id = fields.Many2one(states={'draft': [('readonly', False)],
                                      'open': [('readonly', False)]})

    @api.multi
    def action_invoice_paid(self):
        super_invoices = self.filtered(lambda inv: inv.amount_total != 0)
        return super(AccountInvoice, super_invoices).action_invoice_paid()
