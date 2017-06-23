# -*- coding: utf-8 -*-
# © 2016 Comunitea - Kiko Sánchez <kiko@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models, _


class StockPicking(models.Model):
    _inherit = "stock.picking"

    def show_packs_in_pick(self):
        ids = []
        for op in self.pack_operation_ids:
            ids.append(op.id)
        view_id = self.env['ir.model.data'].xmlid_to_res_id(
            'jim_sale.stock_pack_picks_tree')
        #view_id = self.env.ref('stock_pack_picks_tree').id
        return {
            'domain': "[('id','in', " + str(ids) + ")]",
            'name': _('Packing List'),
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'stock.pack.operation',
            'view_id': view_id,
            'context': False,
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def do_transfer(self):
        res = super(StockPicking, self).do_transfer()
        for pick in self.filtered(lambda picking: picking.pack_operation_ids):
            number_of_packages = []
            for op in pick.pack_operation_ids.filtered(lambda op_id: op_id.result_package_id):
                number_of_packages.append(op.result_package_id.id)
            for op in pick.pack_operation_ids.filtered(lambda op_id: (not op_id.result_package_id and op_id.package_id)):
                number_of_packages.append(op.package_id.id)

            pick.number_of_packages = len(list(set(number_of_packages)))


