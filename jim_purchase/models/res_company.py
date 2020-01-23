# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.exceptions import AccessError, except_orm
from odoo import api, fields, models, _


class ResCompany(models.Model):
    _inherit = 'res.company'

    default_in_type_id = fields.Many2one('stock.picking.type', string='Tipo de entrega por defecto')