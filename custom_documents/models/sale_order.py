# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _


class SaleOrder(models.Model):

    _inherit = "sale.order"

    neutral_document = fields.Boolean()

    # función para separar impuestos,luego la llamamos desde el pedido
    def _get_tax_amount_disaggregated(self):
        self.ensure_one()
        res = {}
        for line in self.order_line:
            base_tax = 0
            for tax in line.tax_id:
                group = tax
                res.setdefault(group, 0.0)
                amount = tax.compute_all(
                    line.price_reduce + base_tax,
                    quantity=line.product_uom_qty,
                    product=line.product_id,
                    partner=self.partner_shipping_id,
                )["taxes"][0]["amount"]
                res[group] += amount
                if tax.include_base_amount:
                    base_tax += tax.compute_all(
                        line.price_reduce + base_tax,
                        quantity=1,
                        product=line.product_id,
                        partner=self.partner_shipping_id,
                    )["taxes"][0]["amount"]
        res = sorted(res.items(), key=lambda l: l[0].sequence)
        res = map(lambda l: (l[0].name, l[1]), res)
        return res

    @api.model
    def create(self, vals):
        order = super(SaleOrder, self).create(vals)
        if "neutral_document" in vals:
            if (
                order.partner_shipping_id
                and not order.partner_shipping_id.is_company
                and not order.partner_shipping_id.parent_id
            ):
                order.partner_shipping_id.active = not vals["neutral_document"]
        return order

    def write(self, vals):
        super(SaleOrder, self).write(vals)
        if "neutral_document" in vals:
            message = _(
                "The Neutral Document field of this sale order has "
                "been modified"
            )
            self.message_post(body=message)
        for order in self:
            if order.neutral_document and order.partner_shipping_id:
                if (
                    not order.partner_shipping_id.is_company
                    and not order.partner_shipping_id.parent_id
                ):
                    order.partner_shipping_id.active = False
        return True


class SaleOrderLine(models.Model):

    _inherit = "sale.order.line"

    name_report = fields.Text(compute="_compute_name_report")

    def _compute_name_report(self):
        for line in self:
            name_report = line.name
            if "[%s]" % line.product_id.default_code in line.name:
                name_report = line.name.replace(
                    "[%s]" % line.product_id.default_code, ""
                )
            line.name_report = name_report

    def _prepare_invoice_line(self, qty):
        res = super(SaleOrderLine, self)._prepare_invoice_line(qty)
        res["promotion_line"] = self.promotion_line
        return res
