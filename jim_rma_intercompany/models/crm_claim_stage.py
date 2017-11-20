# -*- coding: utf-8 -*-
# Copyright 2015-2017 Odoo S.A.
# Copyright 2017 Vicent Cubells <vicent.cubells@tecnativa.com>
# License LGPL-3.0 or later (http://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class CrmClaimStage(models.Model):

    _inherit = "crm.claim.stage"


    default_new = fields.Boolean('New stage')
    default_run = fields.Boolean('Running stage')
    default_done= fields.Boolean('Done stage')