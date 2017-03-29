# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    global_real_stock = fields.Float('Global Real Stock',
                                     compute='_compute_global_stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.")
    global_available_stock = fields.Float('Global Available Stock',
                                          compute='_compute_global_stock',
                                          digits=dp.get_precision
                                          ('Product Unit of Measure'))

    def _compute_global_stock(self):
        global_real_stock = 10.0
        global_available_stock = 20.0
        for product in self:
            product.global_real_stock = global_real_stock
            product.global_available_stock = global_available_stock


class Productroduct(models.Model):
    _inherit = "product.product"

    global_real_stock = fields.Float('Global Real Stock',
                                     compute='_compute_global_stock',
                                     digits=dp.get_precision
                                     ('Product Unit of Measure'),
                                     help="Real stock in all companies.")
    global_available_stock = fields.Float('Global Available Stock',
                                          compute='_compute_global_stock',
                                          digits=dp.get_precision
                                          ('Product Unit of Measure'))

    def _compute_global_stock(self):
        global_real_stock = 1.0
        global_available_stock = 2.0
        for product in self:
            product.global_real_stock = global_real_stock
            product.global_available_stock = global_available_stock
