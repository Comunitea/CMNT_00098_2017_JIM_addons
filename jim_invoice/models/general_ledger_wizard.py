# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models

class GeneralLedgerReportWizard(models.TransientModel):

    _inherit = "general.ledger.report.wizard"

    @api.onchange('company_id')
    def onchange_company_id(self):
        res = super(GeneralLedgerReportWizard, self).onchange_company_id()

        if self.company_id:
            res['domain']['partner_ids'] = [
                '&',
                '|', ('company_id', 'child_of', self.company_id.id),
                ('company_id', '=', False),
                ('company_type', '=', 'company')
                ]
        return res