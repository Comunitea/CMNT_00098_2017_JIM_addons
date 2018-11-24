# -*- coding: utf-8 -*-
# © 2016 Carlos Dauden <carlos.dauden@tecnativa.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import _, api, fields, models
import odoo.addons.decimal_precision as dp


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('order_line.price_total_cancelled')
    def _compute_amount_cancelled(self):
        for order in self:
            order.price_total_cancelled = sum(line.price_total_cancelled for line in order.order_line)

    @api.multi
    def _get_default_cancelled_order_in_risk(self):
        cancelled_order_in_risk = self.env['ir.config_parameter'].get_param('cancelled_order_in_risk', '0') == '1'
        for order in self:
            order.cancelled_order_in_risk = cancelled_order_in_risk


    price_total_cancelled = fields.Monetary(compute='_compute_amount_cancelled', string='Cancelled amount', readonly=True, store=True)
    cancelled_order_in_risk = fields.Boolean('Qty cancelled', compute="_get_default_cancelled_order_in_risk")


    @api.multi
    @api.depends('state', 'partner_id.risk_sale_order_include', 'order_line.invoice_lines.invoice_id.amount_total', 'invoice_status', 'price_total_cancelled', 'order_line.price_total_cancelled')
    def _compute_invoice_amount(self):
        super(SaleOrder, self)._compute_invoice_amount()
        if self.env['ir.config_parameter'].get_param('cancelled_order_in_risk', '0') == '0':
            return
        for order in self.filtered(lambda x: x.state == 'sale' and x.invoice_pending_amount > 0.00):
            order.invoice_pending_amount -= order.price_total_cancelled

    @api.multi
    def action_view_order_lines(self):
        action = super(SaleOrder, self).action_view_order_lines()
        action['context']['cancelled_order_in_risk'] = self.env['ir.config_parameter'].get_param('cancelled_order_in_risk', '0') == '0'
        return action


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    @api.depends('procurement_ids.move_ids.state', 'cancelled_qty')
    def _compute_amount_cancelled(self):
        if self._table == "sale_order_line_template":
            return
        for line in self:
            price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.cancelled_qty, product=line.product_id, partner=line.order_id.partner_shipping_id)
            line.price_total_cancelled = taxes['total_included']

    @api.multi
    @api.depends('procurement_ids.move_ids.state')
    def _get_cancelled_qty(self):
        """Computes the delivered quantity on sale order lines, based on done stock moves related to its procurements
        """
        if self._table == "sale_order_line_template":
            return
        for line in self:
            qty = 0.00
            for move in line.procurement_ids.mapped('move_ids').filtered(lambda r: r.state == 'cancel' and not r.scrapped):
                if move.location_dest_id.usage == "customer":
                    if not move.origin_returned_move_id:
                        qty += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                        #print "Resto del albaran cancelado {}".format(
                        # move.picking_id.name)
                elif move.location_dest_id.usage != "customer" and move.to_refund_so:
                    qty -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    #print "Resto del albaran cancelado {}".format(
                    # move.picking_id.name)
            line.cancelled_qty = qty

    price_total_cancelled = fields.Monetary(compute='_compute_amount_cancelled', string='Cancelled amount', readonly=True, store=True)
    cancelled_qty = fields.Float('Cancelled Quantity', compute='_get_cancelled_qty', digits=dp.get_precision('Product Unit of Measure'), store=True)

class SaleOrderLineTemplate(models.Model):
    _inherit = 'sale.order.line.template'

    price_total_cancelled = fields.Monetary(string='Total (without cancelled)', readonly=True)
    cancelled_qty = fields.Float('Cancelled Quantity', digits=dp.get_precision('Product Unit of Measure'))
