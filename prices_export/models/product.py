# -*- coding: utf-8 -*-
# © 2020 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from datetime import datetime

import logging
_logger = logging.getLogger('--EXPORTACIÓN PRECIOS--')


class ProductProduct(models.Model):

    _inherit = 'product.product'

    # @api.multi
    # def write(self, vals):
    #     # import ipdb; ipdb.set_trace
    #     """
    #     Quizás no tengo que controlar activado desactivado?
    #     Si cambia la categoría A por B, debo buscar los itemes para esta
    #     categoría A
    #     """
    #     res = super(ProductProduct, self).write(vals)
    #     if 'active' in vals:
    #         if vals['active'] == False:
    #             self.set_items_update()
    
    # @api.multi
    # def set_items_update(self):
    #     # import ipdb; ipdb.set_trace
    #     return