# -*- coding: utf-8 -*-
# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, api
from odoo.exceptions import AccessError


class ProductProduct(models.Model):

    _inherit = 'product.product'

class SuppliferInfo(models.Model):
    _inherit = "product.supplierinfo"
    _description = "Information about a product vendor"
    _order = 'product_id asc, sequence, min_qty desc, price'