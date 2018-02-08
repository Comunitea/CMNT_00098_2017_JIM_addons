# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    arancel_percentage = fields.Float()
    arancel = fields.Float(compute='_compute_arancel', store=True)

    @api.depends('price_subtotal', 'quantity', 'arancel_percentage')
    def _compute_arancel(self):
        for line in self:
            if line.arancel_percentage:
                line.arancel = (line.price_subtotal / line.quantity) * (line.arancel_percentage / 100)
            else:
                line.arancel = 0

    @api.model
    def create(self, vals):
        res = super(AccountInvoiceLine, self).create(vals)
        if res.invoice_id and res.invoice_id.state != 'draft':
            raise UserError('Solo se pueden añadir lineas a facturas en '
                            'estado borrador. Descarte los cambios cancele '
                            'la factura y sitúela en '
                            'estado borrador para realizar esta operación')
        return res


class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    delivery_cost = fields.Float()
