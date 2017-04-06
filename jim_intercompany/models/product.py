# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    """ Pull rules """
    _inherit = 'product.template'

    intercompany_price = fields.Float('Intercompany Price',
                                      digits=dp.get_precision('Product Price'))
