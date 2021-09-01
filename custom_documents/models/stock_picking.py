# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api
from datetime import timedelta
from pytz import timezone


class StockPicking(models.Model):

    _inherit = "stock.picking"

    same_day_delivery = fields.Boolean(compute="_compute_same_day_delivery")
    delivery_date = fields.Char(compute="_compute_delivery_date")
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

    def _compute_global_discount_amount(self):
        for picking in self:
            #TODO: Migrar de ser necesario
            # ~ global_discount_lines = picking.sale_id.order_line
            # ~ ep_disc = picking.sale_id.total_early_discount
            # ~ if global_discount_lines or ep_disc:
                # ~ picking.global_discount_amount = (
                    # ~ sum(global_discount_lines.mapped("price_subtotal"))
                    # ~ + ep_disc
                # ~ )
            # ~ else:
            picking.global_discount_amount = 0.0

    #TODO: Migrar de ser necesario
    # ~ def _compute_amount_all(self):
        # ~ res = super(StockPicking, self)._compute_amount_all()
        # ~ for pick in self:
            # ~ if pick.sale_id:
                # ~ delivery_line = pick.sale_id.order_line.filtered(
                    # ~ lambda x: x.product_id.delivery_cost
                # ~ )
                # ~ global_discount_lines = pick.sale_id.order_line
                # ~ if delivery_line:
                    # ~ amount_untaxed = (
                        # ~ sum(
                            # ~ pick.pack_operation_ids.mapped(
                                # ~ "sale_price_subtotal"
                            # ~ )
                        # ~ )
                        # ~ + delivery_line[0].price_subtotal
                        # ~ + sum(global_discount_lines.mapped("price_subtotal"))
                        # ~ + sum(pick.sale_services.mapped("price_subtotal"))
                    # ~ )
                    # ~ amount_tax = (
                        # ~ sum(pick.pack_operation_ids.mapped("sale_price_tax"))
                        # ~ + delivery_line[0].price_tax
                        # ~ + sum(global_discount_lines.mapped("price_tax"))
                        # ~ + sum(pick.sale_services.mapped("price_tax"))
                    # ~ )
                    # ~ pick.update(
                        # ~ {
                            # ~ "amount_untaxed": amount_untaxed,
                            # ~ "amount_tax": amount_tax,
                            # ~ "amount_total": amount_untaxed + amount_tax,
                        # ~ }
                    # ~ )
                # ~ else:
                    # ~ amount_untaxed = (
                        # ~ sum(
                            # ~ pick.pack_operation_ids.mapped(
                                # ~ "sale_price_subtotal"
                            # ~ )
                        # ~ )
                        # ~ + sum(global_discount_lines.mapped("price_subtotal"))
                        # ~ + sum(pick.sale_services.mapped("price_subtotal"))
                    # ~ )
                    # ~ amount_tax = (
                        # ~ sum(pick.pack_operation_ids.mapped("sale_price_tax"))
                        # ~ + sum(global_discount_lines.mapped("price_tax"))
                        # ~ + sum(pick.sale_services.mapped("price_tax"))
                    # ~ )
                    # ~ pick.update(
                        # ~ {
                            # ~ "amount_untaxed": amount_untaxed,
                            # ~ "amount_tax": amount_tax,
                            # ~ "amount_total": amount_untaxed + amount_tax,
                        # ~ }
                    # ~ )
            # ~ elif pick.purchase_id:

                # ~ amount_tax = sum(
                    # ~ pick.pack_operation_ids.mapped("purchase_price_tax")
                # ~ )
                # ~ amount_total = sum(
                    # ~ pick.pack_operation_ids.mapped("purchase_price_total")
                # ~ )
                # ~ val = {
                    # ~ "amount_untaxed": amount_total - amount_tax,
                    # ~ "amount_tax": amount_tax,
                    # ~ "amount_total": amount_total,
                # ~ }

                # ~ pick.update(val)
        # ~ return res

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
