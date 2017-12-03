# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models
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

        domain = [('type', '=', 'product')]
        domain += [('default_code', '!=', '')]
        #domain += [('', '!=', '')]
        product_ids = self.env['product.product'].search(domain)
        if self.tag_ids:
            product_ids = product_ids.filtered(lambda x: self.tag_ids in x.tag_ids)
        if self.categ_ids:
            product_ids = product_ids.filtered(lambda x: x.categ_id == self.categ_ids)

        ids = product_ids.ids
        print len(ids)
        new_sga_file = self.env['sga.file'].check_sga_file('product.product', ids, code='PST', version=3)
        return new_sga_file


