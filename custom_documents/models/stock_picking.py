# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    copy_printing = fields.Boolean("Imprime copia")
    documento_neutro = fields.Boolean()
