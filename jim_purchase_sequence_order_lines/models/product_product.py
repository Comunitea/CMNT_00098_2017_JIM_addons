# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

ORDER_LINE_INC = 1000

from odoo import api, models, fields

class ProductProduct(models.Model):

    _inherit ='product.product'

    @api.multi
    def get_variant_sequence(self, sequence_origin=0):
        new_sequence = 0
        for product in self:
            new_sequence = sequence_origin * ORDER_LINE_INC * ORDER_LINE_INC
            for value in product.attribute_value_ids:
                if value.is_color:
                    new_sequence += value.sequence * ORDER_LINE_INC
                else:
                    new_sequence += value.sequence
        return new_sequence

class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.multi
    def create_variant_ids(self):
        return super(ProductTemplate, self).create_variant_ids()
