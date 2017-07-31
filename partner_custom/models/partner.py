# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    harbor_ids = fields.Many2many("res.harbor", string="Harbors")
    propietary = fields.\
        Char("Propietary", related="company_id.ref", readonly=True)
    web_password = fields.Char("Password web", size=32)
    default_contact_person = fields.Char("Contact person", size=90)
    invoice_in_paper = fields.Boolean()
