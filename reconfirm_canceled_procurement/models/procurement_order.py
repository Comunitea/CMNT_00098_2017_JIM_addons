# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _
from odoo.exceptions import ValidationError

LOCATION_USAGES = ['customer']

class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    active = fields.Boolean(default=True, help="Set archive to true to hide the maintenance request without deleting it.")

class ProcurementOrder(models.Model):

    _inherit = "procurement.order"


    @api.multi
    def reconfirmed_procurement_order(self):
        procs_to_cancel = self.filtered(lambda x:x.state == 'cancel')
        if not procs_to_cancel:
            raise ValidationError(_('None procurement canceled'))
        customer_procs_to_cancel = procs_to_cancel.filtered(lambda x:x.location_id.usage in LOCATION_USAGES)
        if not customer_procs_to_cancel:
            raise ValidationError(_('None procurement in customer location'))
        for procurement in customer_procs_to_cancel:
            procurement.reset_to_confirmed()
        
        for procurement in customer_procs_to_cancel:
            procurement.run()
