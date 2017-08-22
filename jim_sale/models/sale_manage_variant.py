# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import odoo.addons.decimal_precision as dp
from odoo import api, models, fields, _

from odoo.exceptions import ValidationError

class SaleManageVariant(models.TransientModel):
    _inherit = 'sale.manage.variant'


    @api.onchange('product_tmpl_id')
    def _onchange_product_tmpl_id(self):

        context = self.env.context
        record = self.env[context['active_model']].browse(
            context['active_id'])
        if context['active_model'] == 'sale.order.line':
            sale_order = record.order_id
        else:
            sale_order = record
        if sale_order.template_lines:
            if self.product_tmpl_id.id in [x.product_template.id for x in sale_order.template_lines]:
                self.product_tmpl_id = False
                raise ValidationError(
                    _('You must modify this template from template lines in sale order".'))

        return super(SaleManageVariant, self)._onchange_product_tmpl_id()