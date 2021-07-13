# © 2018 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class MrBom(models.Model):

    _inherit = "mrp.bom"

    no_web_stock = fields.Boolean()
