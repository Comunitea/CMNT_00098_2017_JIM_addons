# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, api, _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def confirm_order_background(self, order_id):
        """
        OWERWRITED in order to pass the state to pending or lqdr
        """
        self.browse(order_id).action_lqdr_pending()
