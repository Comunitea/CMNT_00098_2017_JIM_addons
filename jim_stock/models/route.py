# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp

class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    no_stock = fields.Boolean('No Stock', default=False)


