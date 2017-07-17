# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class SaleOrder(models.Model):

    _inherit = 'sale.order'

    copy_printing = fields.Boolean("Imprime copia")
    documento_neutro = fields.Boolean()

#función para separar impuestos,luego la llamamos desde el pedido
    @api.multi
    def _get_tax_amount_disaggregated(self):
        self.ensure_one()
        res = {}
        currency = self.currency_id or self.company_id.currency_id
        for line in self.order_line:
            base_tax = 0
            for tax in line.tax_id:
                group = tax
                res.setdefault(group, 0.0)
                amount = tax.compute_all(
                    line.price_reduce + base_tax,
                    quantity=line.product_uom_qty,
                    product=line.product_id,
                    partner=self.partner_shipping_id)['taxes'][0]['amount']
                res[group] += amount
                if tax.include_base_amount:
                    base_tax += tax.compute_all(
                        line.price_reduce + base_tax, quantity=1,
                        product=line.product_id,
                        partner=self.partner_shipping_id)['taxes'][0]['amount']
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = map(lambda l: (l[0].name, l[1]), res)
        return res
