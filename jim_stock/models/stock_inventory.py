# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models


class StockInventoryLine(models.Model):

    _inherit = "stock.inventory.line"

    # Needed beacause of odoo bug when Start a inventory in a company, when
    # same product inventory is done in other company, and there are MORE THAN
    # one idiom loaded in database.
    # With this we avoid to write this field in inventory_lines belonging to
    # other company
    product_name = fields.Char(readonly=True)


    def _get_quants(self):
        quants = super(StockInventoryLine, self)._get_quants()
        ids = quants.sudo().filtered(lambda x:x.propagated_from_id.company_id.id == self.inventory_id.company_id.id).ids
        return self.env['stock.quant'].browse(ids)
