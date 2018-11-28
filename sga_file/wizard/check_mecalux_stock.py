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
        sga_file_obj = self.env['sga.file']
        hora_inicio = datetime.now()
        not_product = self.get_product_waiting_sga_confirm()
        domain = [('type', '=', 'product'),('active','=',True)]
        domain += [('default_code', '!=', '')]
        if self.categ_ids:
            domain += [('categ_id', '=', self.categ_ids.id)]
        product_ids = self.env['product.product'].search(domain, order='id asc')
        if not_product:
            product_ids -= not_product
        if self.tag_ids:
            product_ids = product_ids.filtered(lambda x: self.tag_ids in x.tag_ids)
        ids = product_ids.sorted(lambda x: x.id).ids
        new_sga_file = sga_file_obj.check_sga_file('product.product', ids, code='PST')
        log_name = u"{}.log".format(new_sga_file.name)
        str = "RESUMEN de generacion del fichero: {}" \
              "\n -- Productos no incluidos: {}" \
              "\n -- Productos incluidos: {}" \
              "\n -- Inicio escritura fichero: {}" \
              "\n -- Fin escritura fichero: {} Tiempo empleado: {}".format(new_sga_file.name, len(not_product), len(ids), hora_inicio, datetime.now(), datetime.now()-hora_inicio)
        sga_file_obj.write_log(str, log_name, False)
        return new_sga_file


    def get_product_waiting_sga_confirm(self, domain= []):

        domain += [('state', '=', 'assigned'), ('sga_state', 'in', ('PM', 'MT', 'MC'))]
        picks = self.env['stock.picking'].sudo().search(domain)
        if picks:
            pick_ids = picks.ids
        else:
            return []

        domain = [('picking_id', 'in', pick_ids)]
        product_ids = self.env['stock.move'].sudo().search(domain).mapped('product_id').sorted(lambda x:x.id)
        return product_ids or []

