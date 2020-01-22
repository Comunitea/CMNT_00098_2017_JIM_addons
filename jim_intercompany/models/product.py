# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models
import odoo.addons.decimal_precision as dp
from odoo.tools import float_is_zero


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    intercompany_price = fields.Float('Intercompany Price',
                                      digits=dp.get_precision('Product Price'))
    no_ic = fields.Boolean('No Intercompany Actions', default=False)

class ProductProduc(models.Model):
    _inherit = 'product.product'

    #HARDCODED!!!!!. REVIEW
    def get_intercompany_price(self, company_id, partner_id):
        # Compañias
        # Jim = 1
        # SE = 8
        # EME = 5
        # Gestibeca = 16
        #partner
        # Jim = 1
        # SE = 18
        # EME = 11

        if not float_is_zero(self.intercompany_price,
                         precision_digits=2):
            return self.intercompany_price
        #Compra realizada desde Jim o SE a EME
        if company_id in (1, 8, 16) and \
                        partner_id == 11:
            pricelist_id = 39  # tarifa de produccion
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
            price = pricelist.get_product_price(self, 1.0,
                                    self.env['res.partner'].browse(partner_id))
            return price
        # debería ser para compras a JIm y SE pero como no tenemsopor
        # defecto otra dejamos esta
        #if purchase_line.order_id.partner_id.id in (1, 18):
        else:
            pricelist_id = 14  # tarifa PVP03
            pricelist = self.env['product.pricelist'].browse(pricelist_id)
            price = pricelist.get_product_price(self, 1.0,
                                    self.env['res.partner'].browse(partner_id))
            return price * 0.90