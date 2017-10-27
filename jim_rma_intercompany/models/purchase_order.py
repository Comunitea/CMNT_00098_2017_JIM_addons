# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrder(models.Model):

    _inherit = "purchase.order"

    claim_id = fields.Many2one("crm.claim", "RMA")

    @api.model
    def _prepare_sale_order_line_data(self, line, company, sale_id):
        res = super(PurchaseOrder, self)._prepare_sale_order_line_data(line, company, sale_id)
        if self.claim_id and self.intercompany:
            route = self.env['stock.location.route'].search([('name', '=', 'RMA IC')])
            if not route:
                raise ValidationError(
                    _('Not RMA IC route created for rma intercompany moves.')
                )
            res['route_id'] = route.id
        return res

