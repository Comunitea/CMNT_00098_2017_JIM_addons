# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.exceptions import AccessError, except_orm
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.depends ('product_id', 'product_qty')
    def _get_line_dimension(self):
        for line in self:
            line.line_volume = 0.00
            line.line_weight = 0.00
            if line.product_id:
                line.line_volume = line.product_id.volume * line.product_qty
                line.line_weight = line.product_id.weight * line.product_qty

    line_volume = fields.Float("Volume", compute="_get_line_dimension")
    line_weight = fields.Float("Weight", compute="_get_line_dimension")
    line_info = fields.Char("Line info")
    web_global_stock = fields.Float(related="product_id.web_global_stock")

    @api.multi
    def show_line_info(self):
        #Comentado por si no vale la solucion
        #view_id = self.env.ref('jim_purchase.purchase_order_form_line_info').id

        return {
            'name': _('Show info line Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
            #'views': [(view_id, 'form')],
            #'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    order_volume = fields.Float("Volume", compute="_compute_dimensions")
    order_weight = fields.Float("Weight", compute="_compute_dimensions")
    expediente = fields.Char("Expediente")


    @api.depends('order_line.line_volume', 'order_line.line_weight')
    def _compute_dimensions(self):
        for order in self:
            order_volume = 0.00
            order_weight = 0.00
            for line in order.order_line:
                order_volume += line.line_volume
                order_weight += line.line_weight
            order.update({
                'order_volume': order_volume,
                'order_weight': order_weight,
            })

    @api.multi
    def show_line_info(self):
        view_id = self.env.ref('jim_purchase.purchase_order_form_line_info').id

        return {
            'name': _('Show info line Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }

    @api.multi
    def _add_supplier_to_product(self):
        res = super(PurchaseOrder, self)._add_supplier_to_product()
        for line in self.order_line:
            partner = self.partner_id if not self.partner_id.parent_id else \
                self.partner_id.parent_id
            if line.product_id.seller_ids.filtered(lambda x: x.name == partner):
                seller_id = line.product_id.seller_ids.filtered(lambda x: x.name == partner)
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id

                try:
                    seller_id.write({'price': self.currency_id.compute(line.price_unit, currency)})
                except AccessError:  # no write access rights -> just ignore
                    break
