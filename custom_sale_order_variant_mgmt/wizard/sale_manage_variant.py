# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _
from odoo.exceptions import ValidationError


class SaleManageVariant(models.TransientModel):
    _inherit = 'sale.manage.variant'

    @api.multi
    def button_transfer_to_order(self):
        context = self.env.context
        record = self.env[context['active_model']].browse(
            context['active_id'])
        if context['active_model'] == 'sale.order.line.template':
            template = record
        else:
            template_vals = {
                'product_template': self.product_tmpl_id.id,
                'order_id': self._context.get('active_id', False),
                'name': self.product_tmpl_id.name_get()[0][1]}
            new_template_line = self.env['sale.order.line.template'].new(
                template_vals)
            new_template_line.onchange_template()
            new_template_line.product_id_change()
            vals = new_template_line._convert_to_write(
                    new_template_line._cache)
            # vals.update(template_vals)
            vals.update(
                {'product_uom_qty': 0, 'price_unit': 0, 'purchase_price': 0})
            template = self.env['sale.order.line.template'].create(vals)


        super(SaleManageVariant,
              self.with_context(
                template_line=template.id, active_model='sale.order',
                active_id=template.order_id.id)).button_transfer_to_order()
        if not template.order_lines:
            template.unlink()
        else:           
            # Calculate total qty an new prices (grom specific prices)
            sum_qty = 0
            for line in template.order_lines:
                sum_qty += line.product_uom_qty
                if context['active_model'] != 'sale.order.line.template':
                    line.product_uom_change()  # Update prices depend of qty
                line._onchange_discount()  # Update variant pricelist discount.
            # Get total qty
            template.product_uom_qty = sum_qty



    @api.multi
    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):

        self.variant_line_ids = [(6, 0, [])]
        template = self.product_tmpl_id
        context = self.env.context
        record = self.env[context['active_model']].browse(
            context['active_id'])
        if context['active_model'] == 'sale.order.line':
            sale_order = record.order_id
        elif context['active_model'] == 'sale.order.line.template':
            sale_order = record.order_id
        else:
            sale_order = record
            if sale_order.template_lines:
                if self.product_tmpl_id.id in [x.product_template.id for x in sale_order.template_lines]:
                    self.product_tmpl_id = False
                    raise ValidationError(
                        _('You must modify this template from template lines in sale order.'))
        num_attrs = len(template.attribute_line_ids)
        if not template or not num_attrs:
            return
        line_x = template.attribute_line_ids[0]
        line_y = False if num_attrs == 1 else template.attribute_line_ids[1]
        lines = []
        for value_x in line_x.value_ids:
            for value_y in line_y and line_y.value_ids or [False]:
                # Filter the corresponding product for that values
                values = value_x
                if value_y:
                    values += value_y
                product = template.product_variant_ids.filtered(
                    lambda x: not(values - x.attribute_value_ids))[:1]
                order_line = sale_order.order_line.filtered(
                    lambda x: x.product_id == product)[:1]
                lines.append((0, 0, {
                    'product_id': product,
                    'disabled': not bool(product),
                    'value_x': value_x,
                    'value_y': value_y,
                    'product_uom_qty': order_line.product_uom_qty,
                }))
        self.variant_line_ids = lines
