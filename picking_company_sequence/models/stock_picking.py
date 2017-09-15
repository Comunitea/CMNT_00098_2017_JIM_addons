# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

class StockPickingType(models.Model):

    _inherit = "stock.picking.type"

    property_sequence_id = fields.Many2one('ir.sequence', 'Reference Sequence (Company)', company_dependent=True)


class StockPicking(models.Model):

    _inherit = "stock.picking"

    @api.model
    def create(self, vals):
        defaults = self.default_get(['name', 'picking_type_id'])
        if vals.get('picking_type_id', False):
            picking_type_id = self.env['stock.picking.type'].with_context(force_company=vals['company_id']).browse(vals['picking_type_id'])[0]
            property_sequence = picking_type_id and picking_type_id.property_sequence_id
            if property_sequence:
                if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id', defaults.get('picking_type_id')):
                    vals['name'] = property_sequence.next_by_id()

        return super(StockPicking, self).create(vals)

