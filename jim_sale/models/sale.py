# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _

# from odoo.addons import decimal_precision as dp
# from odoo.tools import float_compare
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _get_origin_sale(self):
        for order in self:
            for line in order.sudo().order_line:
                if line.move_dest_IC_id:
                    order.sale_origin = line.move_dest_IC_id.origin
                    continue

    # We have to overdrive, because of we need to set the states order here,
    # so we can display it in widget statusbar_visible
    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("proforma", "Proforma"),
            ("lqdr", "Pending LQDR"),
            ("progress_lqdr", "Progress LQDR"),
            ("pending", "Revision Pending"),
            ("progress", "Confirm in Progress"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ]
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
        required=True,
        change_default=True,
        index=True,
        track_visibility="always",
        domain=[("is_company", "=", True)],
    )
    chanel = fields.Selection(selection_add=[("web", "WEB")])
    work_to_do = fields.Text("Trabajo a realizar")
    route_id = fields.Many2one(
        "stock.location.route",
        string="Force Route",
        domain=[("sale_selectable", "=", True)],
    )
    lqdr_state = fields.Selection(
        [
            ("no_lqdr", ""),
            ("lqdr_no", "LQDR No tramitado"),
            ("lqdr_si", "LQDR Tramitado"),
            ("lqdr_issue", "LQDR Incidencia"),
        ],
        string="Estado LQDR",
        default="no_lqdr",
    )
    sale_origin = fields.Char("Venta a Cliente", compute=_get_origin_sale)
    partner_shipping_id = fields.Many2one(
        states={
            "draft": [("readonly", False)],
            "sent": [("readonly", False)],
            "progress": [("readonly", False)],
            "lqdr": [("readonly", False)],
            "progress_lqdr": [("readonly", False)],
            "pending": [("readonly", False)],
            "sale": [("readonly", False)],
        }
    )
    company_id = fields.Many2one(
        readonly=True,
        states={"draft": [("readonly", False)], "sent": [("readonly", False)]},
    )
    scheduled_order = fields.Boolean("Scheduled Order")

    @api.model
    def create_web(self, vals):
        partner = self.env["res.partner"].browse(vals["partner_id"])
        vals.update({"payment_term_id": partner.property_payment_term_id.id})
        vals.update({"payment_mode_id": partner.customer_payment_mode_id.id})
        vals.update({"pricelist_id": partner.property_product_pricelist.id})
        vals.update(
            {"fiscal_position_id": partner.property_account_position_id.id}
        )
        # Descuento financiero
        commercial_partner = partner.commercial_partner_id
        early_payment_discount = 0
        if not partner.property_payment_term_id:
            early_discs = commercial_partner.early_payment_discount_ids
            if early_discs:
                early_payment_discount = early_discs[0].early_payment_discount

        else:
            early_discs = (
                commercial_partner.early_payment_discount_ids.filtered(
                    lambda x: x.payment_term_id == self.payment_term_id
                )
            )
            if early_discs:
                early_payment_discount = early_discs[0].early_payment_discount
            else:
                early_discs = commercial_partner.early_payment_discount_ids
                if early_discs:
                    early_payment_discount = early_discs[
                        0
                    ].early_payment_discount
                else:
                    early_discs = self.env[
                        "account.early.payment.discount"
                    ].search(
                        [
                            ("partner_id", "=", False),
                            (
                                "payment_term_id",
                                "=",
                                partner.property_payment_term_id.id,
                            ),
                        ]
                    )
                    if early_discs:
                        early_payment_discount = early_discs[
                            0
                        ].early_payment_discount
        vals.update({"early_payment_discount": early_payment_discount})

        for line in vals["order_line"]:
            dict_line = line[2]
            product = self.env["product.product"].browse(
                dict_line["product_id"]
            )
            route_id = product.route_ids and product.route_ids[0]
            lqdr = product.lqdr
            dict_line.update({"route_id": route_id.id})
            dict_line.update({"lqdr": lqdr})
        res = super(SaleOrder, self).create(vals)
        return res.id

    def action_invoice_create(self, grouped=False, final=False):
        invs = super(SaleOrder, self).action_invoice_create(grouped, final)
        self.env["account.invoice"].browse(
            invs
        ).button_compute_early_payment_disc()
        return invs

    @api.onchange("partner_id")
    def onchange_partner_id_warning(self):
        if not self.partner_id:
            return
        dict_warning = super(SaleOrder, self).onchange_partner_id_warning()
        partner = self.partner_id
        if partner.property_payment_term_id.prepayment:

            if not dict_warning:
                title = ("Warning for %s") % partner.name
                message = "PAGO POR ANTICIPADO"
                warning = {
                    "title": title,
                    "message": message,
                }
                return {"warning": warning}
            else:
                dict_warning["warning"]["message"] = (
                    "PAGO POR ANTICIPADO "
                    "\n\n" + dict_warning["warning"]["message"]
                )
        return dict_warning

    def action_proforma(self):
        for order in self:
            order.state = "proforma"
        return True

    def action_confirm(self):
        """
        Avoid check risk in action confirm
        """
        ctx = self._context.copy()
        for order in self:
            ctx.update(bypass_risk=True, force_company=order.company_id.id)
            super(SaleOrder, order.with_context(ctx)).action_confirm()
            order.picking_ids.write({"scheduled_order": order.scheduled_order})
        return True

    @api.model
    def get_risk_msg(self, order_id):
        """
        Called before confirm_order_from_ui
        """
        exception_msg = ""
        if not self.env.context.get("bypass_risk", False):
            order = self.browse(order_id)
            partner = order.partner_id.commercial_partner_id
            if partner.risk_exception:
                exception_msg = _("Financial risk exceeded.\n")
            elif partner.risk_sale_order_limit and (
                (partner.risk_sale_order + order.amount_total)
                > partner.risk_sale_order_limit
            ):
                exception_msg = _(
                    "This sale order exceeds the sales orders risk.\n"
                )
            elif partner.risk_sale_order_include and (
                (partner.risk_total + order.amount_total)
                > partner.credit_limit
            ):
                exception_msg = _(
                    "This sale order exceeds the financial risk.\n"
                )
        return exception_msg

    def action_lqdr_option(self):
        warning_msg = []
        for order in self:
            # Risk check
            exception_msg = self.get_risk_msg(order.id)
            if exception_msg:
                partner = order.partner_id.commercial_partner_id
                return (
                    self.env["partner.risk.exceeded.wiz"]
                    .create(
                        {
                            "exception_msg": exception_msg,
                            "partner_id": partner.id,
                            "origin_reference": "%s,%s"
                            % ("sale.order", order.id),
                            "continue_method": "action_lqdr_option",
                        }
                    )
                    .action_show()
                )

            self.confirm_checks()
            if order.order_line.filtered("product_id.lqdr"):
                order.state = "lqdr"
                order.lqdr_state = "lqdr_no"
            else:
                order.state = "pending"
            date_order = fields.Datetime.now()
            order.date_order = date_order
            if (
                order.partner_id.sale_warn_msg
                or order.partner_id.property_payment_term_id.prepayment
            ):
                # si se confirman varias ventas se montará un mensaje
                # con todos los avisos
                order_msg = ""
                if order.partner_id.property_payment_term_id.prepayment:
                    order_msg += "PAGO POR ANTICIPADO \n\n"
                if order.partner_id.sale_warn_msg:
                    order_msg += order.partner_id.sale_warn_msg
                if len(self) > 1:
                    warning_msg.append("%s: %s" % (order.name, order_msg))
                else:
                    warning_msg.append(order_msg)
            if warning_msg:
                return {
                    "type": "ir.actions.act_window.message",
                    "title": _("Customer warning"),
                    "message": "\n".join(warning_msg),
                }
            else:
                return True
        return

    def action_lqdr_ok(self):
        for order in self:
            order.state = "pending"
            order.lqdr_state = "lqdr_si"
        return True

    def action_pending_ok(self):
        for order in self:
            order.set_requested_date()
            order.action_sale()
        return True

    def action_sale(self):
        for order in self:
            # confirmation_date = order.confirmation_date
            order.action_confirm()
            # order.confirmation_date = confirmation_date
            picking_out = order.picking_ids.filtered(
                lambda x: x.picking_type_id.code == "outgoing"
            )
            picking_out.write({"ready": True})
        return True

    @api.onchange("warehouse_id")
    def _onchange_warehouse_id(self):
        """
        Avoid change warehouse_company_id
        """
        return

    def apply_route_to_order_lines(self):

        for order in self:
            if order.state == "done":
                raise ValueError(
                    "No puedes asignar rutas a un pedido confirmado"
                )
            for line in order.template_lines:
                line.route_id = order.route_id
            for line in self.order_line:
                line.route_id = self.route_id

    def action_view_delivery(self):
        action = super(SaleOrder, self).action_view_delivery()
        # if 'domain' in action and action['domain']:
        #    action['domain'].append(('picking_type_id.name', 'not like', '%Inter%'))
        return action

    def confirm_checks(self):
        if not self.partner_shipping_id.country_id:
            raise ValidationError("No puedes confirmar sin pais de envío")
        if (
            self.partner_shipping_id.country_id.id == 69
            and not self.partner_shipping_id.state_id
        ):
            raise ValidationError("No puedes confirmar sin provincia de envío")

    def action_cancel_wzd(self):

        view = self.env.ref("jim_sale.wzd_sale_order_cancel_view")
        wiz = self.env["wzd.sale.order.cancel"].create({"sale_id": self.id})
        ctx = dict(self._context)
        ctx.update({"default_sale_id": self.id})

        return {
            "name": "Confirmación de cancelación",
            "type": "ir.actions.act_window",
            "view_type": "form",
            "view_mode": "form",
            "res_model": "wzd.sale.order.cancel",
            "views": [(view.id, "form")],
            "view_id": view.id,
            "res_id": wiz.id,
            "target": "new",
            "context": ctx,
        }

    def set_requested_date(self):
        if self.requested_date:
            requested_date = datetime.strptime(
                self.requested_date, "%Y-%m-%d %H:%M:%S"
            )

            self.requested_date = fields.Datetime.from_string(
                requested_date.strftime("%Y-%m-%d") + " 06:00:00"
            ) - timedelta(days=1)
        if not self.requested_date:
            time_deadline = " 19:30:00"
            datetime_limit = fields.Date.today() + time_deadline

            if datetime_limit > fields.Datetime.now():
                date_planned = fields.Datetime.from_string(datetime_limit)
            else:
                date_planned = fields.Datetime.from_string(
                    fields.Date.today() + " 04:00:00"
                ) + timedelta(days=1)

            self.requested_date = date_planned

    def write(self, vals):
        if "partner_shipping_id" in vals:
            for order in self.filtered(lambda x: x.partner_shipping_id):
                message = "Se ha modificado la dirección de envío <a href=# data-oe-model=res.partner data-oe-id={}>{}</a>".format(
                    order.partner_shipping_id.id,
                    order.partner_shipping_id.name,
                )
                order.message_post(body=message)
        for sale in self:
            if "partner_shipping_id" in vals and sale.procurement_group_id:
                sale.procurement_group_id.partner_id = vals[
                    "partner_shipping_id"
                ]
                pickings = self.env["stock.picking"].search(
                    [
                        ("group_id", "=", sale.procurement_group_id.id),
                        ("partner_id", "=", sale.partner_shipping_id.id),
                    ]
                )
                pickings.write({"partner_id": vals["partner_shipping_id"]})
                message = "Se ha modificado la dirección de envío <a href=# data-oe-model=res.partner data-oe-id={}>{}</a>.<br/>Se cambiará en los albaranes no hechos".format(
                    order.partner_shipping_id.id,
                    order.partner_shipping_id.name,
                )
                order.message_post(body=message)
        return super(SaleOrder, self).write(vals)

    def check_sale_stock(self):
        self.ensure_one
        message = ""
        for line in self.order_line:
            if line.global_available_stock != line.product_id.web_global_stock:
                line.write(
                    {
                        "global_available_stock": line.product_id.global_available_stock
                    }
                )
            if line.global_available_stock < line.product_uom_qty:
                message = "{}\n{}: Stock: {} / Pedido: {}".format(
                    message,
                    line.name,
                    line.global_available_stock,
                    line.product_uom_qty,
                )
        if message:
            title = "Productos sin stock:"
            message = "Listado: {}".format(message)
            warning = {
                "type": "ir.actions.act_window.message",
                "title": title,
                "message": message,
            }
            return warning
        return False


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    state = fields.Selection(
        [
            ("draft", "Quotation"),
            ("sent", "Quotation Sent"),
            ("lqdr", "LQDR"),
            ("pending", "Pending Approval"),
            ("sale", "Sales Order"),
            ("done", "Locked"),
            ("cancel", "Cancelled"),
        ]
    )

    lqdr = fields.Boolean(related="product_id.lqdr", store=False)

    @api.onchange("product_id")
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        # if self.product_id.route_ids:
        self.route_id = (
            self.order_id.route_id
            or self.product_id.route_ids
            and self.product_id.route_ids[0]
        )

        return res

    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)
        # Search for specific prices in variants
        qty = product._context.get("quantity", 1.0)
        partner_id = self.order_id.partner_id.id
        date = self.order_id.date_order
        customer_price = self.env["customer.price"].get_customer_price(
            partner_id, product, qty, date=date
        )
        if customer_price:
            return customer_price
        return res

    def action_procurement_create(self):

        old_state = self.order_id.state
        self.order_id.state = "sale"
        new_procs = self._action_procurement_create()
        self.order_id.state = old_state
        return new_procs

    def _action_procurement_create(self):
        return super(SaleOrderLine, self)._action_procurement_create()

    def _prepare_order_line_procurement(self, group_id=False):

        vals = super(SaleOrderLine, self)._prepare_order_line_procurement(
            group_id=group_id
        )
        for line in self.filtered("order_id.requested_date"):
            date_planned = fields.Datetime.from_string(
                line.order_id.requested_date
            ) - timedelta(days=line.order_id.company_id.security_lead)
            vals.update(
                {
                    "date_planned": fields.Datetime.to_string(date_planned),
                }
            )
        return vals


class SaleOrderLineTemplate(models.Model):

    _inherit = "sale.order.line.template"

    lqdr = fields.Boolean(related="product_template.lqdr", store=False)

    def create_template_procurements(self):
        for line in self.order_lines:
            line.action_procurement_create()

        return {"type": "ir.actions.client", "tag": "reload"}

    @api.depends("invoice_lines.invoice_id.state", "invoice_lines.quantity")
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        return False

    @api.depends(
        "qty_invoiced", "qty_delivered", "product_uom_qty", "order_id.state"
    )
    def _get_to_invoice_qty(self):
        return False

    @api.depends(
        "state",
        "product_uom_qty",
        "qty_delivered",
        "qty_to_invoice",
        "qty_invoiced",
    )
    def _compute_invoice_status(self):
        return False
