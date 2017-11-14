# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
from odoo.tools.safe_eval import safe_eval


class CrmClaimRmaMakeRefund(models.TransientModel):

    _inherit = 'crm.claim.rma.make.refund'

    ic_refunds = fields.Boolean("IC refunds", default=True)


    @api.multi
    def make_refund(self):

        self.ensure_one()
        claim = self.env['crm.claim'].browse(self._context.get('claim_id'))
        ctx = self._context.copy()
        ctx.update(force_company=claim.company_id.id,
                   company_id=claim.company_id.id)
        lines_to_invoice = claim.claim_line_ids.filtered(lambda x:not x.refund_line_id)
        if claim.invoice_status != 'to invoice' or not lines_to_invoice:
            raise exceptions.UserError(_('Nothing to invoice'))

        if claim.ic:
            invoice_obj = self.env['account.invoice'].sudo().with_context(ctx)
            invoice_line_obj = self.env['account.invoice.line'].sudo().with_context(ctx)
        else:
            invoice_obj = self.env['account.invoice'].with_context(ctx)
            invoice_line_obj = self.env['account.invoice.line'].with_context(ctx)


        if claim.claim_type.name == "Customer":
            type = ('in_refund')
            move_field = 'move_out_id'
        else:
            type = ('out_refund')
            move_field = 'move_in_id'

        n_reference = len(self.env['account.invoice'].search([('claim_id', '=', claim.id)]))
        if claim.rma_number:
            reference = claim.rma_number + '/[%s]' % claim.code
        else:
            reference = claim.code
        if n_reference:
            reference = reference + ' (%s)'%n_reference
        invoice_vals = {
            'partner_id': claim.partner_id.id,
            'type': (type),
            'date_invoice': self.invoice_date,
            'company_id': claim.company_id.id,
            'state': 'draft',
            'claim_id': claim.id,
            'reference': reference,
            'origin': claim.code
        }
        invoice = invoice_obj.new(invoice_vals)
        invoice._onchange_partner_id()
        invoice_vals = invoice._convert_to_write(invoice._cache)
        new_invoice = invoice_obj.create(invoice_vals)
        picking_ids = self.env['stock.picking']
        for line in lines_to_invoice:
            invoice_line_vals = {'product_id': line.product_id.id,
                 'name': line.name,
                 'quantity': line.product_returned_quantity,
                 'price_unit': line.unit_sale_price,
                 'invoice_id': new_invoice.id}

            invoice_line = invoice_line_obj.new(invoice_line_vals)
            invoice_line._onchange_product_id()
            invoice_line_vals = invoice_line._convert_to_write(invoice_line._cache)
            new_line = invoice_line_obj.create(invoice_line_vals)
            new_line.write({'price_unit': line.unit_sale_price,
                            'name': line.name})
            line.refund_line_id = new_line
            picking_ids |= line[move_field].picking_id

        new_invoice.compute_taxes()
        new_invoice.compute_amount()
        new_invoice.picking_ids = picking_ids
        if claim.claim_ids:
            domain_ic = [('claim_id', '=', claim.id), ('ic', '=', True)]
            claim_ic_ids = self.env['crm.claim'].search(domain_ic)
            if claim_ic_ids:
                for claim_ic in claim_ic_ids:
                    ctx = self._context.copy()
                    ctx.update({'claim_id': claim_ic.id})
                    self.with_context(ctx).make_refund()


        result = self.env.ref('account.action_invoice_tree1').read()[0]
        invoice_domain = [('id', 'in', claim.invoice_ids.ids)]
        result['domain'] = invoice_domain
        return result

