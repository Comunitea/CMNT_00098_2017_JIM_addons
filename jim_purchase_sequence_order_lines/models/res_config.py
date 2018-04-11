# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class PurchaseConfigSettings(models.TransientModel):
    _inherit = 'purchase.config.settings'

    group_reorder_purchase_line = fields.Selection([
        (0, 'NOT Allow reorder by sequence template'),
        (1, 'Allow reorder by sequence template')
        ], "Template sequence reorder", implied_group='jim_purchase_sequence_order_lines.group_reorder_purchase_line')