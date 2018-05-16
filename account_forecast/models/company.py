# -*- coding: utf-8 -*-
# Copyright 2018 Santi Argüeso, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResCompany(models.Model):

    _inherit = "res.company"

    forecast_journal_id = fields.Many2one('account.journal',
                                          string="Forecast Journal")