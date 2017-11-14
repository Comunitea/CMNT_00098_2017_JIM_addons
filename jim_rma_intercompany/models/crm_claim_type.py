# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import fields, models


class CrmClaimType(models.Model):

    _inherit = 'crm.claim.type'

    return_claim = fields.Many2one('crm.claim.type', 'Return claim')