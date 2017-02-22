# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResHarbor(models.Model):
    '''Harbor'''

    _name = "res.harbor"
    _description = __doc__
    _order = "name asc"

    name = fields.Char("Name", required=True)
    code = fields.Char("Code")
    country_id = fields.Many2one("res.country", "Country")
    
