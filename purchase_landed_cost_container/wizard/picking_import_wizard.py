# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import models, fields, api


class PickingImportWizard(models.TransientModel):
    _inherit = "picking.import.wizard"

    container = fields.Many2one('shipping.container')
    supplier = fields.Many2one(required=False)

    def _get_domain(self):
        domain = [('location_id.usage', '=', 'supplier'),
                  ('state', '=', 'done')]
        if self.supplier:
            domain.append(('partner_id', 'child_of', self.supplier.id))
        if self.container:
            domain.append(('shipping_container_id', '=', self.container.id))
        return domain

    @api.onchange('supplier')
    def onchange_supplier(self):
        return {'domain': {'pickings': self._get_domain()}}

    @api.onchange('container')
    def onchange_container(self):
        return {'domain': {'pickings': self._get_domain()}}
