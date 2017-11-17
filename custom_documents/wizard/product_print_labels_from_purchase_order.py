# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api, exceptions, _


class ProductPrinstLabelsFromPicking(models.TransientModel):

    _name = 'product.print.labels.from.purchase'

    @api.multi
    def print_label(self):
        self.ensure_one()
        datas = {'ids': self.env['purchase.order'].browse(
            self._context['active_ids']).mapped('order_line.id')}
        return self.env['report'].get_action(
            self, 'custom_documents.product_label_report',
            data=datas)
