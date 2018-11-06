# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError

ORDER_LINE_INC = 1000

class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'
    _order = 'order_id desc, template_sequence, sequence, id'

    template_sequence = fields.Integer('Template Sequence')

    @api.model
    def create(self, vals):
        line = super(PurchaseOrderLine, self).create(vals)
        template_sequence = max(line.order_id.mapped('order_line.template_sequence')) + 10
        new_sequence = 0
        cent = 100
        for value in line.product_id.attribute_value_ids:
            if value.attribute_id.is_color:
                new_sequence += value.id * ORDER_LINE_INC
            else:
                new_sequence += value.sequence * cent
            cent = 1
        line.write({'template_sequence': template_sequence,
                     'sequence': new_sequence})
        return line

    @api.multi
    def write(self, vals):
        return super(PurchaseOrderLine, self).write(vals)

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        for val in res:
            val.update({
                'sequence': self.sequence,
                'template_sequence': self.template_sequence
            })
        return res

    @api.multi
    @api.onchange('template_sequence')
    def onchange_template_sequence(self):
        return


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    @api.model
    def reorder_sequence_lines(self):
        lines = self.order_line
        ctx = dict(self._context.copy())
        ctx.update({'update_sequence': True})
        while lines:
            line_0 = lines[0]
            product_template = line_0.product_id.product_tmpl_id.id
            template_lines = lines.filtered(lambda x: x.product_id.product_tmpl_id.id == product_template)
            template_lines.with_context(ctx).write({'template_sequence': line_0.template_sequence})
            lines = lines - template_lines

        for line in self.order_line:
            product_id = line.product_id

    @api.multi
    @api.onchange('order_line')
    def onchange_template_sequence(self):

        for order in self:
            order.reorder_sequence_lines()

