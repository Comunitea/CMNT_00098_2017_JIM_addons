# Copyright 2017 Javier Colmenero, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, models


class WizResolveQuant(models.TransientModel):
    _name = "wiz.resolve.quant"

    @api.multi
    def resolve(self):
        self.ensure_one()
        self.env["stock.quant"].sudo().soluciona()
