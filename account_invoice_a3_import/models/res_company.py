# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):

    _inherit = "res.company"

    a3_company_code = fields.Char("A3 company code",
                                  help="Code to identify the company in the "
                                       "A3 importation.")
