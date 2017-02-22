# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields
import odoo.addons.decimal_precision as dp


class ResPartner(models.Model):

    _inherit = "res.partner"

    harbor_ids = fields.Many2many("res.harbor", string="Harbors")
    propietary = fields.\
        Char("Propietary", default=lambda self: self.env.user.company_id.ref)
    partner_discount = fields.Float("Partner discount", default=0.0,
                                    digits=dp.get_precision('Discount'))
