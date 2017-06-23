# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProductTemplate(models.Model):

    _inherit = "product.template"

    tariff = fields.Float('Tariff', digits=(16,2))
    volume = fields.Float(
        'Volume', compute='_compute_volume', inverse='_set_volume',
        help="The volume in m3.", store=True, digits=(10, 6))


class ProductProduct(models.Model):

    _inherit = "product.product"

    volume = fields.Float('Volume', help="The volume in m3.", digits=(10, 6))


class ProductPackaging(models.Model):

    _inherit = "product.packaging"

    def compute_product_dimensions(self):
        if self.qty == 0:
            raise ValidationError(_("Check quantity !!!!"))
        self.product_tmpl_id.weight = self.max_weight / self.qty
        self.product_tmpl_id.volume = self.height * self.width * self.length / (self.qty * 1000000)