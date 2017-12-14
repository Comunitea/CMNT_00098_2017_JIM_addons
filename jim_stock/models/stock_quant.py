# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp



class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.one
    def _quant_reconcile_negative(self, move):
        new_self = self.filtered(lambda x: not x.reservation_id)
        return super(StockQuant, new_self)._quant_reconcile_negative(move)

    def quants_get_reservation(self, qty, move, pack_operation_id=False, lot_id=False, company_id=False, domain=None,
                               preferred_domain_list=None):
        '''
        Esto elimina el dominio que permite quiatr reservas a movimientos reservados
        '''

        if preferred_domain_list:
            fallback_domain2 = ['&', ('reservation_id', '!=', move.id), ('reservation_id', '!=', False)]
            if fallback_domain2 in preferred_domain_list:
                preferred_domain_list.remove(fallback_domain2)

        return super(StockQuant, self).quants_get_reservation(qty, move, pack_operation_id, lot_id, company_id, domain, preferred_domain_list)