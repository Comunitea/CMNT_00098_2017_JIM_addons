# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    no_propagate_term = fields.Boolean('No Propagate payment terms')
