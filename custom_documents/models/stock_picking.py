# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import timedelta
from pytz import timezone
from odoo.addons import decimal_precision as dp


class StockPicking(models.Model):

    _inherit = "stock.picking"

    neutral_document = fields.Boolean(
        "Neutral Document", related="sale_id.neutral_document"
    )
    operator = fields.Char("Operator")
    same_day_delivery = fields.Boolean(compute="_compute_same_day_delivery")
    delivery_date = fields.Char(compute="_compute_delivery_date")
    delivery_amount = fields.Monetary(compute="_compute_delivery_amount")
    global_discount_amount = fields.Monetary(
        compute="_compute_global_discount_amount"
    )
    min_date_date = fields.Date(compute="_compute_min_date_date")
    date_done_date = fields.Date(compute="_compute_min_date_date")
    sale_services = fields.Many2many(
        "sale.order.line",
        "stock_picking_sale_order_line_services_rel",
        "picking_id",
        "sale_id",
        compute="_compute_sale_services",
    )
    purchase_currency_id = fields.Many2one(
        related="purchase_id.currency_id", string="Currency"
    )

    @api.depends("scheduled_date")
    def _compute_min_date_date(self):
        for pick in self:
            pick.min_date_date = (
                pick.scheduled_date
                and pick.scheduled_date.split(" ")[0]
                or False
            )
            if pick.date_done:
                pick.date_done_date = pick.date_done.split(" ")[0]
            else:
                pick.date_done_date = pick.min_date_date

    # Si el albaran  se finalizó antes de las 17:30 entre semana se envía el
    # mismo día.
    def _compute_same_day_delivery(self):
        for pick in self:
            if pick.date_done:
                same_day_delivery = True
                date_done = (
                    fields.Datetime.from_string(pick.date_done)
                    .replace(tzinfo=timezone("Etc/UTC"))
                    .astimezone(timezone(pick._context.get("tz", "Etc/UTC")))
                )
                if (
                    date_done.hour > 17
                    or (date_done.hour == 17 and date_done.minute > 30)
                    or date_done.isoweekday() in (6, 7)
                ):
                    same_day_delivery = False
                pick.same_day_delivery = same_day_delivery

    def _compute_delivery_date(self):
        # Si no se envía el mismo día se comprueba que el día de envío no
        # sea ni sabado ni domingo
        for pick in self:
            if pick.date_done:
                if pick.same_day_delivery:
                    pick.delivery_date = pick.date_done
                else:
                    date_done = fields.Datetime.from_string(pick.date_done)
                    next_date = date_done + timedelta(days=1)
                    delivery_date = next_date
                    if next_date.isoweekday() == 6:
                        delivery_date = next_date + timedelta(days=2)
                    elif next_date.isoweekday() == 7:
                        delivery_date = next_date + timedelta(days=1)
                    pick.delivery_date = delivery_date

    def _compute_delivery_amount(self):
        for picking in self:
            delivery_line = picking.sale_id.order_line.filtered(
                lambda x: x.product_id.delivery_cost
            )
            if delivery_line:
                picking.delivery_amount = delivery_line[0].price_subtotal
            else:
                picking.delivery_amount = 0.0

    def _compute_global_discount_amount(self):
        for picking in self:
            global_discount_lines = picking.sale_id.order_line.filtered(
                lambda x: x.promotion_line
            )
            ep_disc = picking.sale_id.total_early_discount
            if global_discount_lines or ep_disc:
                picking.global_discount_amount = (
                    sum(global_discount_lines.mapped("price_subtotal"))
                    + ep_disc
                )
            else:
                picking.global_discount_amount = 0.0

    def _compute_amount_all(self):
        res = super(StockPicking, self)._compute_amount_all()
        for pick in self:
            if pick.sale_id:
                delivery_line = pick.sale_id.order_line.filtered(
                    lambda x: x.product_id.delivery_cost
                )
                global_discount_lines = pick.sale_id.order_line.filtered(
                    lambda x: x.promotion_line
                )
                if delivery_line:
                    amount_untaxed = (
                        sum(
                            pick.pack_operation_ids.mapped(
                                "sale_price_subtotal"
                            )
                        )
                        + delivery_line[0].price_subtotal
                        + sum(global_discount_lines.mapped("price_subtotal"))
                        + sum(pick.sale_services.mapped("price_subtotal"))
                    )
                    amount_tax = (
                        sum(pick.pack_operation_ids.mapped("sale_price_tax"))
                        + delivery_line[0].price_tax
                        + sum(global_discount_lines.mapped("price_tax"))
                        + sum(pick.sale_services.mapped("price_tax"))
                    )
                    pick.update(
                        {
                            "amount_untaxed": amount_untaxed,
                            "amount_tax": amount_tax,
                            "amount_total": amount_untaxed + amount_tax,
                        }
                    )
                else:
                    amount_untaxed = (
                        sum(
                            pick.pack_operation_ids.mapped(
                                "sale_price_subtotal"
                            )
                        )
                        + sum(global_discount_lines.mapped("price_subtotal"))
                        + sum(pick.sale_services.mapped("price_subtotal"))
                    )
                    amount_tax = (
                        sum(pick.pack_operation_ids.mapped("sale_price_tax"))
                        + sum(global_discount_lines.mapped("price_tax"))
                        + sum(pick.sale_services.mapped("price_tax"))
                    )
                    pick.update(
                        {
                            "amount_untaxed": amount_untaxed,
                            "amount_tax": amount_tax,
                            "amount_total": amount_untaxed + amount_tax,
                        }
                    )
            elif pick.purchase_id:

                amount_tax = sum(
                    pick.pack_operation_ids.mapped("purchase_price_tax")
                )
                amount_total = sum(
                    pick.pack_operation_ids.mapped("purchase_price_total")
                )
                val = {
                    "amount_untaxed": amount_total - amount_tax,
                    "amount_tax": amount_tax,
                    "amount_total": amount_total,
                }

                pick.update(val)
        return res

    @api.depends("sale_id")
    def _compute_sale_services(self):
        for picking in self:
            picking.sale_services = picking.sale_id.order_line.filtered(
                lambda x: x.product_id.type == "service"
                and not x.product_id.delivery_cost
            )

    def action_open_purchases_valued_ops(self):
        action = self.env.ref(
            "custom_documents.action_open_view_valued_stock_pack_op_tree"
        ).read()[0]
        action["domain"] = [("id", "in", self.pack_operation_ids.ids)]
        action["context"] = {
            "default_picking_id": self.id,
        }
        return action


class StockMove(models.Model):
    _inherit = "stock.move"

    name_report = fields.Char(compute="_compute_name_report")

    def _compute_name_report(self):
        for line in self:
            name_report = line.name
            if "[%s]" % line.product_id.default_code in line.name:
                name_report = line.name.replace(
                    "[%s]" % line.product_id.default_code, ""
                )
            line.name_report = name_report

    @api.onchange("product_id")
    def onchange_product_id(self):
        """Se hereda el onchange para establecer correctamente el nombre"""
        res = super(StockMove, self).onchange_product_id()
        product = self.product_id.with_context(
            lang=self.partner_id.lang or self.env.user.lang
        )
        if product:
            self.name = product.name_get()[0][1]
        return res


# TODO: Migrar, no existe el modelo stock_pack_operation
# ~ class StockPackOperation(models.Model):
# ~ _inherit = "stock.pack.operation"

# ~ purchase_line = fields.Many2one(
# ~ comodel_name="purchase.order.line",
# ~ compute="_compute_purchase_order_line_fields",
# ~ string="Related order line",
# ~ )
# ~ purchase_tax_id = fields.Many2many(
# ~ comodel_name="account.tax",
# ~ compute="_compute_purchase_order_line_fields",
# ~ string="Taxes",
# ~ )
# ~ purchase_tax_description = fields.Char(
# ~ compute="_compute_purchase_order_line_fields", string="Tax Description"
# ~ )
# ~ purchase_price_unit = fields.Float(
# ~ compute="_compute_purchase_order_line_fields",
# ~ digits=dp.get_precision("Product Price"),
# ~ string="purchase price unit",
# ~ )
# ~ purchase_discount = fields.Float(
# ~ compute="_compute_purchase_order_line_fields",
# ~ digits=dp.get_precision("Discount"),
# ~ string="purchase discount (%)",
# ~ )
# ~ purchase_price_subtotal = fields.Float(
# ~ compute="_compute_purchase_order_line_fields", string="Price subtotal"
# ~ )
# ~ purchase_price_tax = fields.Float(
# ~ compute="_compute_purchase_order_line_fields", string="Taxes"
# ~ )
# ~ purchase_price_total = fields.Float(
# ~ compute="_compute_purchase_order_line_fields", string="Total"
# ~ )
# ~ qty_delivered = fields.Float(
# ~ "Delivered qty",
# ~ default=0.0,
# ~ digits=dp.get_precision("Product Unit of Measure"),
# ~ compute="_get_qty_delivered",
# ~ )

# ~ def _get_qty_delivered(self):
# ~ for operation in self:
# ~ operation.qty_delivered = (
# ~ operation.qty_done or operation.product_qty
# ~ )

# ~ def _compute_purchase_order_line_fields(self):
# ~ for operation in self:
# ~ purchase_lines = operation.mapped(
# ~ "linked_move_operation_ids.move_id.purchase_line_id"
# ~ )
# ~ operation.update(operation.purchase_lines_values(purchase_lines))

# ~ def purchase_lines_values(self, purchase_lines):
# ~ if len(purchase_lines) <= 1:
# ~ price_unit = purchase_lines.price_unit
# ~ discount = 0.00
# ~ else:
# ~ price_unit = purchase_lines[0].price_unit
# ~ discount = 0.00

# ~ purchase_line = purchase_lines[:1]
# ~ purchase_tax = purchase_line.taxes_id
# ~ taxes = purchase_tax.compute_all(
# ~ price_unit=price_unit,
# ~ currency=purchase_line.currency_id,
# ~ quantity=self.qty_delivered,
# ~ product=purchase_line.product_id,
# ~ partner=purchase_line.order_id.partner_id,
# ~ )
# ~ if purchase_line.company_id.tax_calculation_rounding_method == (
# ~ "round_globally"
# ~ ):
# ~ price_tax = sum(
# ~ t.get("amount", 0.0) for t in taxes.get("taxes", [])
# ~ )
# ~ else:
# ~ price_tax = taxes["total_included"] - taxes["total_excluded"]
# ~ val = {
# ~ "purchase_line": purchase_line,
# ~ "purchase_tax_id": purchase_tax,
# ~ "purchase_tax_description": ", ".join(
# ~ map(lambda x: (x.description or x.name), purchase_tax)
# ~ ),
# ~ "purchase_price_unit": price_unit,
# ~ "purchase_discount": discount,
# ~ "purchase_price_subtotal": taxes["total_excluded"],
# ~ "purchase_price_tax": price_tax,
# ~ "purchase_price_total": taxes["total_included"],
# ~ }

# ~ return val
