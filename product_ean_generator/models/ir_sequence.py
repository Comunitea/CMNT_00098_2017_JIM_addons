# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class IrSequence(models.Model):
    _inherit = "ir.sequence"

    upper_limit = fields.Integer(
        string="Limit", help="Upper limit for this sequence"
    )

    def _next_do(self):
        if self.upper_limit > 0 and self.upper_limit < self.number_next_actual:
            raise ValidationError("Limit sequence")
        return super(IrSequence, self)._next_do()
