# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResPartner(models.Model):

    _inherit = "res.partner"

    consolidate = fields.Boolean("Consolidate", company_dependent=True,
                                 help="Allow consolidation when invoicing")

    def _find_accounting_partner(self, partner):
        ''' Find the partner for which the accounting entries will be created '''
        if partner.consolidate and partner.parent_id:
            return partner.parent_id.commercial_partner_id
        else:
            if not partner.parent_id:
                return partner.commercial_partner_id
            else:
                if partner.parent_id.consolidate and \
                        partner.parent_id.parent_id:
                    return partner.parent_id.parent_id
                else:
                    return partner.commercial_partner_id

        return partner.commercial_partner_id
