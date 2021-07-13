# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ProductTag(models.Model):

    _inherit = "product.tag"

    web = fields.Boolean("Web", default=True)
