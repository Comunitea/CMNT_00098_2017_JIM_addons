# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
import time
from odoo.addons import decimal_precision as dp
from odoo.tools import float_compare
from odoo.exceptions import ValidationError

class SaleOrder(models.Model):
    _inherit = "sale.order"

    # We have to overdrive, because of we need to set the states order here,
    # so we can display it in widget statusbar_visible
    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('proforma', 'Proforma'),
        ('lqdr', 'Pending LQDR'),
        ('progress_lqdr', 'Progress LQDR'),
        ('pending', 'Revision Pending'),
        ('progress', 'Confirm in Progress'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    chanel = fields.Selection(selection_add=[('web', 'WEB')])
    work_to_do = fields.Text('Trabajo a realizar')
    route_id = fields.Many2one('stock.location.route', string='Force Route', domain=[('sale_selectable', '=', True)])

    @api.model
    def create_web(self, vals):
        partner = self.env['res.partner'].browse(vals['partner_id'])
        vals.update({'payment_term_id': partner.property_payment_term_id.id})
        vals.update({'payment_mode_id': partner.customer_payment_mode_id.id})
        vals.update({'pricelist_id': partner.property_product_pricelist.id})
        vals.update({'fiscal_position_id':
                    partner.property_account_position_id.id})
        for line in vals['template_lines']:
            dict_line = line[2]
            product = self.env['product.product'].\
                browse(dict_line['product_id'])
            route_id = product.route_ids and product.route_ids[0]
            lqdr = product.lqdr
            dict_line.update({'route_id': route_id.id})
            dict_line.update({'lqdr': lqdr})
        return super(SaleOrder, self).create(vals)

    @api.onchange('partner_id')
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
                    'title': title,
                    'message': message,
                }
                return {'warning': warning}
            else:
                dict_warning['warning']['message'] = "PAGO POR ANTICIPADO " \
                                                     "\n\n" + \
                                                     dict_warning['warning'][
                                                         'message']
        return dict_warning

    @api.multi
    def action_proforma(self):
        for order in self:
            order.state = 'proforma'
        return True

    @api.multi
    def action_lqdr_option(self):
        for order in self:
            self.confirm_checks()

            if order.order_line.filtered('product_id.lqdr'):
                order.state = 'lqdr'
            else:
               order.state = 'pending'
        return True

    @api.multi
    def action_lqdr_ok(self):
        for order in self:
            order.state = 'pending'
        return True

    @api.multi
    def action_pending_ok(self):
        for order in self:
            order.action_sale()
        return True

    @api.multi
    def action_sale(self):
        for order in self:
            order.action_confirm()
            picking_out = order.picking_ids.filtered(lambda x: x.picking_type_id.code == 'outgoing')
            picking_out.write({'ready': True})
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Avoid change warehouse_company_id
        """
        return


    def apply_route_to_order_lines(self):

        for order in self:
            if order.state == 'done':
                raise ValueError("No puedes asignar rutas a un pedido confirmado")
            for line in order.template_lines:
                line.route_id = order.route_id
            for line in self.order_line:
                line.route_id = self.route_id

    @api.multi
    def action_view_delivery(self):
        '''
        TODO HARDCODEADO
        Añado para filtrar intercompañia

        '''
        action = super(SaleOrder, self).action_view_delivery()
        if 'domain' in action and action['domain']:
            action['domain'].append(('picking_type_id.name', 'not like', '%Inter%'))

        return action

    def confirm_checks(self):
        if self.partner_shipping_id.country_id and self.partner_shipping_id.country_id.name.encode('UTF-8') == "%s"%"España":
            if not self.partner_shipping_id.state_id:
                raise ValidationError("No puedes confirmar sin provincia de envío")

class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"


    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('lqdr', 'LQDR'),
        ('pending', 'Pending Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    lqdr = fields.Boolean(related="product_id.lqdr", store=False)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        #if self.product_id.route_ids:
        self.route_id = self.order_id.route_id or self.product_id.route_ids and self.product_id.route_ids[0]

        return res

    @api.multi
    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)
        # Search for specific prices in variants
        qty = product._context.get('quantity', 1.0)
        vals = {}
        partner_id = self.order_id.partner_id.id
        date = self.order_id.date_order
        customer_price = self.env['customer.price'].\
                    get_customer_price(partner_id, product, qty, date=date)
        if customer_price:
            return customer_price
        return res

    @api.multi
    def action_procurement_create(self):
        old_state = self.order_id.state
        self.order_id.state = 'sale'
        new_procs = self._action_procurement_create()
        self.order_id.state = old_state
        return new_procs

    @api.multi
    def _action_procurement_create(self):
        return super(SaleOrderLine, self)._action_procurement_create()


class SaleOrderLineTemplate(models.Model):

    _inherit = 'sale.order.line.template'

    lqdr = fields.Boolean(related="product_template.lqdr", store=False)

    @api.multi
    def create_template_procurements(self):
        for line in self.order_lines:
            line.action_procurement_create()
        return True

    @api.depends('invoice_lines.invoice_id.state', 'invoice_lines.quantity')
    def _get_invoice_qty(self):
        """
        Compute the quantity invoiced. If case of a refund, the quantity invoiced is decreased. Note
        that this is the case only if the refund is generated from the SO and that is intentional: if
        a refund made would automatically decrease the invoiced quantity, then there is a risk of reinvoicing
        it automatically, which may not be wanted at all. That's why the refund has to be created from the SO
        """
        return False

    @api.depends('qty_invoiced', 'qty_delivered', 'product_uom_qty',
                 'order_id.state')
    def _get_to_invoice_qty(self):
        return False

    @api.depends('state', 'product_uom_qty', 'qty_delivered', 'qty_to_invoice',
                 'qty_invoiced')
    def _compute_invoice_status(self):
        return False