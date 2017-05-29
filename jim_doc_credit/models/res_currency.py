# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class ResCurrency(models.Model):

    _inherit = 'res.currency'

    lname = fields.Char("Currency name")
