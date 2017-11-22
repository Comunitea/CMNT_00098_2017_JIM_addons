# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
from odoo.tools.safe_eval import safe_eval


class CrmClaimRmaMakeBatchRefund(models.TransientModel):

    _name = 'crm.claim.rma.make.batch.refund'

    def _default_description(self):
        return self.env.context.get('description', _('RMA Invoice'))

    description = fields.Char(default=_default_description, required=True)
    invoice_date = fields.Date("Invoice date", default=fields.Datetime.now)
    from_invoice_date = fields.Date("From date")
    to_invoice_date = fields.Date("To date")
    partner_id = fields.Many2one("res.partner", "Customer")
    company_id = fields.Many2one("res.company", "Company")
    claim_ids = fields.Many2many("crm.claim", string="Claim RMA")
    claim_line_ids = fields.Many2many(
        'claim.line',
        string='Claim lines')

    @api.model
    def default_get(self, fields):
        ctx = self._context.copy()
        domain = [('id', 'in', ctx.get('active_ids'))]
        claim_ids = self.env['crm.claim'].search(domain)

        if not all(x.stage_id.default_run for x in claim_ids):
            raise exceptions.UserError('No están todas las reclamaciones en estado correcto')
        if claim_ids and claim_ids[0].company_id != self.env.user.company_id:
            raise exceptions.UserError(_('Not in %s' % claim_ids[0].sudo().company_id.name))
        res = super(CrmClaimRmaMakeBatchRefund, self).default_get(fields)
        if claim_ids:
            partner_id = claim_ids[0].partner_id
            company_id = claim_ids[0].company_id
            claim_type = claim_ids[0].claim_type

            if not any(claim.claim_type.id == claim_type.id for claim in claim_ids):
                raise exceptions.UserError(_('Not all rma have the same type'))
            if not any(claim.partner_id.id == partner_id.id for claim in claim_ids):
                raise exceptions.UserError(_('Not all rma have the same partner'))
            if not(claim.company.id == company_id.id for claim in claim_ids):
                raise exceptions.UserError(_('Not all rma have the same company'))

            picks_domain = [('claim_id', 'in', claim_ids.ids)]
            picks = self.env['stock.picking'].search(picks_domain)
            if not all(x.state=='done' for x in picks):
                raise exceptions.UserError('No están todas las reclamaciones en estado correcto')

            from_invoice_date = min(pick.date_done for pick in picks)
            to_invoice_date = max(pick.date_done for pick in picks)
            line_domain = [('claim_id', 'in', claim_ids.ids),
                           ('state', '=', 'treated'),
                           ('refund_line_id', '=', False),
                           '|', ('move_in_id', '!=', False), ('move_out_id', '!=', False)]
            claim_line_ids = self.env['claim.line'].search(line_domain)

            res['claim_line_ids'] = map(lambda x: (4, x), claim_line_ids.ids)
            res['partner_id'] = partner_id.id
            res['company_id'] = company_id.id
            res['from_invoice_date'] = from_invoice_date
            res['to_invoice_date'] = to_invoice_date
            res['claim_ids'] = ctx.get('active_ids')

        return res


    @api.multi
    def make_batch_refund(self):
        if self.company_id != self.env.user.company_id:
            raise exceptions.UserError(_('Not in %s' % self.company_id.name))
        ctx = self._context.copy()
        ctx.update(force_company=self.company_id.id,
                   company_id=self.company_id.id)


        lines_to_invoice = self.claim_line_ids
        invoice_obj = self.env['account.invoice'].with_context(ctx)
        invoice_line_obj = self.env['account.invoice.line'].with_context(ctx)

        if self.claim_ids[0].claim_type.name == "Customer":
            type = ('in_refund')
            move_field = 'move_out_id'
        else:
            type = ('out_refund')
            move_field = 'move_in_id'
        #Creo una factura
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'type': (type),
            'date_invoice': self.invoice_date,
            'company_id': self.company_id.id,
            'state': 'draft',
            'claim_ids': self.claim_ids,
            'origin': ' '.join([x.code for x in self.claim_ids]),
        }
        invoice = invoice_obj.new(invoice_vals)
        invoice._onchange_partner_id()
        invoice_vals = invoice._convert_to_write(invoice._cache)
        new_invoice = invoice_obj.create(invoice_vals)

        stage = self.claim_ids[0]._stage_find(state='done')

        picking_ids = self.env['stock.picking']
        for line in lines_to_invoice:
            invoice_line_vals = \
                {'product_id': line.product_id.id,
                 'name': line.name,
                 'quantity': self.get_claim_line_qty_to_invoice(line) or line.product_returned_quantity,
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

        self.claim_ids.write({
            'invoice_id': new_invoice.id,
            'stage_id': stage
            })
        if not new_invoice or new_invoice and not new_line:
            raise exceptions.UserError(_(''))
        result = self.env.ref('account.action_invoice_tree1').read()[0]
        result['domain'] = [('id', '=', new_invoice.id)]
        return result

    @api.multi
    def get_claim_line_qty_to_invoice(self, line):
        """Computes the returned quantity on rma claim lines, based on done stock moves related to its pickings
        """

        qty = 0.0
        if line.claim_id.claim_type.name == 'Customer':
            picks = line.claim_id.picking_ids.filtered\
                (lambda x: x.claim_id == line.claim_id and
                           (x.location_id.usage == "customer" or x.location_dest_id.usage == "customer"))
            moves = picks.move_lines.filtered(lambda x: x.claim_line_id == line.id)
            qty = 0.0
            for move in moves:
                if move.location_dest_id.usage == "customer":
                    qty += move.product_qty
                elif move.location_id.usage == "customer" and move.to_refund_so:
                    qty -= move.product_qty
            line.qty_to_invoice = qty

        elif line.claim_id.claim_type.name == 'Supplier':
            picks = line.claim_id.picking_ids.filtered\
                (lambda x: x.claim_id == line.claim_id and
                           (x.location_id.usage == "supplier" or x.location_dest_id.usage == "supplier"))
            moves = picks.move_lines.filtered(lambda x:x.claim_line_id == line.id)

            qty = 0.0
            for move in moves:
                if move.location_dest_id.usage == "supplier":
                    qty += move.product_qty
                elif move.location_id.usage == "supplier" and move.to_refund_so:
                    qty -= move.product_qty
            line.qty_to_invoice = qty
        return qty