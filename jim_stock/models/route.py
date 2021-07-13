# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import models, fields


class StockLocationRoute(models.Model):
    _inherit = "stock.location.route"

    no_stock = fields.Boolean(default=False)
    virtual_type = fields.Boolean()
