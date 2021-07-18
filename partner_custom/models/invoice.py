# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class AccountMove(models.Model):

    _inherit = "account.move"

    invoice_in_paper = fields.Boolean(
        related="commercial_partner_id.invoice_in_paper", readonly=True
    )
