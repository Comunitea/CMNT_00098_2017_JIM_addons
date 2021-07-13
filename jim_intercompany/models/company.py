# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _


class ResCompany(models.Model):

    _inherit = "res.company"

    no_ic = fields.Boolean("No Intercompany action rule", default=False)
