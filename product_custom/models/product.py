# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):

    _inherit = "product.template"

    tariff = fields.Float('Tariff', digits=(16, 2))
    volume = fields.Float(
        'Volume', compute='_compute_volume', inverse='_set_volume',
        help="The volume in m3.", store=True, digits=(10, 6))


class ProductProduct(models.Model):

    _inherit = "product.product"

    volume = fields.Float('Volume', help="The volume in m3.", digits=(10, 6))

    # def apply_package_dimensions(self):


class ProductPackaging(models.Model):

    _inherit = "product.packaging"

    def compute_product_dimensions(self):
        if self.qty == 0:
            raise ValidationError(_("Check quantity !!!!"))
        weight = 0.0000
        volume = 0.000000
        for product in self.product_tmpl_id.product_variant_ids:
            product.weight = self.max_weight / self.qty
            weight += product.weight
            product.volume = self.height * self.width * \
                self.length / (self.qty * 1000000)
            volume += product.volume

        self.product_tmpl_id.weight = weight / self.product_variant_count
        self.product_tmpl_id.volume = volume / self.product_variant_count

        return True


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    legacy_code = fields.Char("Legacy code", size=18)


class ProductAttributeValue(models.Model):
    _inherit = "product.attribute.value"

    legacy_code = fields.Char("Legacy code", size=18)


class ProductTag(models.Model):
    _inherit = "product.tag"

    legacy_code = fields.Char("Legacy code", size=18)
