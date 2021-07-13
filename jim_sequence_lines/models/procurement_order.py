# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo import models, api

#TODO: Migrar, el modelo no existe ya. Pero quizás no se siga esta estrategia para el multicompany
# ~ class ProcurementOrder(models.Model):
    # ~ _inherit = "procurement.order"

    # ~ @api.model
    # ~ def _run_move_create(self, procurement):
        # ~ res = super(ProcurementOrder, self)._run_move_create(procurement)

        # ~ if procurement.sale_line_id.sequence:
            # ~ res.update(
                # ~ {
                    # ~ "sequence": procurement.sale_line_id.sequence,
                    # ~ "template_sequence": procurement.sale_line_id.template_sequence,
                # ~ }
            # ~ )

        # ~ return res
