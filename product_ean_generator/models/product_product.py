# -*- coding: utf-8 -*-
# Copyright 2017 Kiko Sánchez, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
#import barcode#

DEFAULT_PRE = "843540%"



class ProductTemplate(models.Model):

    _inherit = 'product.template'

    @api.multi
    def asign_barcode(self):
        for template in self:
            template.product_variant_ids.asign_barcode()


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.multi
    def write(self, vals):
        # Comprobamos si hay movimientos. No podemos por el tema de Mecalux
        if vals.get('barcode', False):
            for product in self:
                if product.stock_move_ids and False:
                    raise ValidationError(_("You can change barcode because this product has moves"))
        return super(ProductProduct, self).write(vals)

    def next_barcode(self):

        def __sumdigits(chk, start=0, end=1, step=2, mult=1):
            return reduce(lambda x, y: int(x) + int(y), list(chk[start:end:step])) * mult

        def eanCheckDigit(chk):
            """Returns the checksum digit of an EAN-13/8 code"""
            if chk.isdigit() and len(chk) == 12:
                m0 = 1
                m1 = 3
                _len = 12
                t = 10 - ((__sumdigits(chk, start=0, end=_len, mult=m0) + __sumdigits(chk, start=1, end=_len, mult=m1)) % 10) % 10

                if t == 10:
                    return 0
                else:
                    return t
            return None
        sequence = self.env.ref('product_ean_generator.seq_product_ean_auto')
        ean12 = sequence.next_by_id()
        return '%s%s'%(ean12, eanCheckDigit(str(ean12)))


    def next_barcode2(self):

        def ean_checksum(ean):
            code = list(ean)
            if len(code) != 12:
                return -1
            oddsum = evensum = total = 0
            code = code[:-1]  # Remove checksum
            for i in range(len(code)):
                if i % 2 == 0:
                    evensum += int(code[i])
                else:
                    oddsum += int(code[i])
            total = oddsum * 3 + evensum
            return int((10 - total % 10) % 10)

        sequence = self.env.ref('product_ean_generator.seq_product_ean_auto')

        ean12 = sequence.next_by_id()
        return '%s%s'%(ean12, ean_checksum(str(ean12)))


    @api.model
    def create(self, vals):
        barcode = vals.get('barcode', False)
        if barcode == 'ASIGNAR':
            vals['barcode'] = self.next_barcode()
        return super(ProductProduct, self).create(vals)


    @api.multi
    def asign_barcode(self):
        for product in self.filtered(lambda s: s.barcode == "ASIGNAR" or not s.barcode):
            product.barcode = product.next_barcode()

