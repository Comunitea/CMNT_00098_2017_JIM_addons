# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html



from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class WizCheckMecaluxStock(models.TransientModel):

    _name = "wiz.check.mecalux.stock"

    location_id = fields.Many2one('stock.location', string="Location to regularize")
    tag_ids = fields.Many2one('product.tag')
    categ_ids = fields.Many2one('product.category')
    zero_qty = fields.Boolean('Zero qty')
    no_zero_qty = fields.Boolean('No zero qty')
    neg_qty = fields.Boolean("Neg qty")


    def regularize(self):
        print "Articulos no incluidos en regularización:\n\n"
        not_product = self.get_product_waiting_sga_confirm()

        domain = [('type', '=', 'product'),('active','=',True)]
        domain += [('default_code', '!=', '')]
        if self.categ_ids:
            domain += [('categ_id', '=', self.categ_ids.id)]
        #if not_product:
        #    domain += [('id', 'not in', not_product)]

        product_ids = self.env['product.product'].search(domain, order='id asc')
        if not_product:
            product_ids -= not_product
        if self.tag_ids:
            product_ids = product_ids.filtered(lambda x: self.tag_ids in x.tag_ids)


        ids = product_ids.sorted(lambda x: x.id).ids

        print "Articulos incluidos en regularización: {}\n\n.{}".format(len(ids), ids)

        print "RESUMEN: \n -- Productos no incluidos: {}\n -- Productos Incluidos: {}. \n -- Inicio escritura fichero: {}".format(len(not_product), len(ids), datetime.now())
        new_sga_file = self.env['sga.file'].check_sga_file('product.product', ids, code='PST')
        print " -- Fin escritura de  {}: {}.".format(new_sga_file.name, datetime.now())
        return new_sga_file


    def get_product_waiting_sga_confirm(self, domain= []):

        domain += [('state', '=', 'assigned'), ('sga_state', 'in', ('PM', 'MT', 'MC'))]
        picks = self.env['stock.picking'].sudo().search(domain)
        if picks:
            pick_ids = picks.ids
        else:
            return []
        #print "------------- Albaranes pendientes: {} \n {}".format(len(pick_ids), pick_ids)
        domain = [('picking_id', 'in', pick_ids)]
        #product_ids = [item['product_id'][0] for item in self.env['stock.move'].sudo().search_read(domain, ['id', 'product_id'])]
        product_ids = self.env['stock.move'].sudo().search(domain).mapped('product_id').sorted(lambda x:x.id)
        #print "------------- Productos no incluidos: {} \n {}".format(len(product_ids), product_ids.ids)
        return product_ids or []

