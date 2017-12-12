# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models


class StockLocation(models.TransientModel):

    _name = "wiz.regularize.location"

    location_id = fields.Many2one('stock.location', string="Location to regularize")

    def regularize(self):

        self.ensure_one()
        loc_id = self.location_id.id
        domain = [('company_id', '=', self.env.user.company_id.id),
                  ('reservation_id', '=', False),
                  ('location_id', '=', loc_id)
                  ]
        domain += [('qty', '<', 2)]
        domain += [('qty', '>', -2)]
        location_regularize = 29
        quants = self.env['stock.quant'].search(domain, order='qty asc')

        pick_vals = self.get_reg_pick_val(location_regularize, loc_id)

        neg_pick = self.env['stock.picking'].create(pick_vals)
        pick_vals = self.get_reg_pick_val(loc_id, location_regularize)

        pos_pick = self.env['stock.picking'].create(pick_vals)

        cont = len(quants)
        for quant in quants.filtered(lambda x:x.qty < 0):
            print "%s - Quant para %s, qty %s" %(cont, quant.product_id.display_name, quant.qty)
            cont -= 1
            move_vals = self.env['stock.move'].new(
                self.get_mov_vals(neg_pick, quant.product_id.id, -quant.qty, neg_pick.location_id,
                                  neg_pick.location_dest_id))
            move_vals.onchange_product_id()
            move_vals.product_uom_qty = -quant.qty
            new_move_vals = move_vals._convert_to_write(move_vals._cache)
            neg_pick.move_lines.create(new_move_vals)

        for quant in quants.filtered(lambda x:x.qty>0):
            print "%s - Quant para %s, qty %s"%(cont, quant.product_id.display_name, quant.qty)
            cont -= 1
            move_vals = self.env['stock.move'].new(
                self.get_mov_vals(neg_pick, quant.product_id.id, quant.qty, pos_pick.location_id, pos_pick.location_dest_id))
            move_vals.onchange_product_id()
            move_vals.product_uom_qty = quant.qty
            new_move_vals = move_vals._convert_to_write(move_vals._cache)
            pos_pick.move_lines.create(new_move_vals)

        return {
            'name': '%s' % neg_pick.name,
            'view_type': 'form',
            'view_mode': 'tree,form',
            'res_model': 'stock.picking',
            'domain': [('id', 'in', [neg_pick.id, pos_pick.id])],
            'type': 'ir.actions.act_window',
        }

    def get_mov_vals(self, pick, product_id, qty, location_id, location_dest_id):
        vals = {
            'product_id': product_id,
            'product_uom_qty': qty,
            'picking_id': pick.id,
            'location_id': location_id,
            'location_dest_id': location_dest_id.id

        }
        return vals
    def get_reg_pick_val(self, location_id, location_dest_id):
        vals = {
            'partner_id': self.env.user.company_id.partner_id.id,
            'picking_type_id': 5,
            'location_id': location_id,
            'location_dest_id': location_dest_id,
        }
        return vals

    def regularize_quants(self):
        loc_id = self.location_id.id
        domain = [('company_id', '=', self.env.user.company_id.id),
                  ('reservation_id', '=', False),
                  ('location_id', '=', loc_id)
                  ]

        location_regularize = 29
        flds=['product_id', 'qty']
        quants = self.env['stock.quant'].read_group(domain, flds, 'product_id')
        quants = [quant for quant in quants if quant['qty'] == 0]
        cont = len(quants)
        for quant in quants:
            cont -= 1
            if quant['qty'] == 0:
                print "%s Trato %s"%(cont, quant['product_id'][1])
                domain_pos = [('qty', '>', 0)] + quant['__domain']
                quant_to_check_ids = self.env['stock.quant'].search(domain_pos)

                for quant_to_check in quant_to_check_ids:
                    print "Quant nº %s"%quant_to_check.id
                    res = quant_to_check.sudo()._quant_reconcile_negative(False)


        domain_neg = [('qty', '<', 0)] + domain
        quants = self.env['stock.quant'].read_group(domain_neg, flds, 'product_id')
        cont = len(quants)
        for quant in quants:
            cont -= 1
            print "%s Trato %s" % (cont, quant['product_id'][1])
            qty_neg = quant['qty']
            domain_pos = [('qty','>', 0), ('product_id', '=', quant['product_id'][1])] + domain
            quant_to_check_ids = self.env['stock.quant'].search(domain_pos, order = "qty desc")
            for quant_pos in quant_to_check_ids:

                if quant_pos.qty >= qty_neg:
                    res = quant_pos.sudo()._quant_reconcile_negative(False)
                    qty_neg = 0

                else:
                    res = quant_pos.sudo()._quant_reconcile_negative(False)
                    qty_neg -= quant_pos.qty

                if qty_neg <= 0:
                    break


