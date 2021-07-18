# © 2016 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api, _
from odoo.exceptions import UserError

import odoo.addons.decimal_precision as dp


class StockQuant(models.Model):

    _inherit = "stock.quant"

    def _quant_reconcile_negative(self, move):
        new_self = self.filtered(lambda x: not x.reservation_id)
        return super(StockQuant, new_self)._quant_reconcile_negative(move)

    def quants_get_reservation(
        self,
        qty,
        move,
        pack_operation_id=False,
        lot_id=False,
        company_id=False,
        domain=None,
        preferred_domain_list=None,
    ):
        """
        Esto elimina el dominio que permite quiatr reservas a movimientos reservados
        """

        if preferred_domain_list:
            fallback_domain2 = [
                "&",
                ("reservation_id", "!=", move.id),
                ("reservation_id", "!=", False),
            ]
            if fallback_domain2 in preferred_domain_list:
                preferred_domain_list.remove(fallback_domain2)

        return super(StockQuant, self).quants_get_reservation(
            qty,
            move,
            pack_operation_id,
            lot_id,
            company_id,
            domain,
            preferred_domain_list,
        )

    @api.model
    def quants_get_preferred_domain(
        self,
        qty,
        move,
        ops=False,
        lot_id=False,
        domain=None,
        preferred_domain_list=[],
    ):
        """This function tries to find quants for the given domain and move/ops, by trying to first limit
        the choice on the quants that match the first item of preferred_domain_list as well. But if the qty requested is not reached
        it tries to find the remaining quantity by looping on the preferred_domain_list (tries with the second item and so on).
        Make sure the quants aren't found twice => all the domains of preferred_domain_list should be orthogonal
        """
        if move.inventory_id:
            fallback_domain2 = [
                ("reservation_id.inventory_id", "!=", move.inventory_id.id)
            ]
            if fallback_domain2 in preferred_domain_list:
                preferred_domain_list.remove(fallback_domain2)
        return super(StockQuant, self).quants_get_preferred_domain(
            qty, move, ops, lot_id, domain, preferred_domain_list
        )
