# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html


from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

#ADDR_LINE1=30
#ADDR_LINE2=30
#CITY=25
#STATE=2
#COUNTRY=15
#ZIP=10
#CONTA
#....

class SGAProductCategory(models.Model):

    _inherit="product.category"
    sga_producttype_code = fields.Char("Sga Producttype Code", size=12)
    sga_parent_producttype_code= fields.Char(related="parent_id.sga_producttype_code")



class SGAContainerTypeCode(models.Model):
    _name ="sga.containertype"


    name = fields.Char("SGA container type code", size=10)
    sga_desc_containertype_code = fields.Char("SGA container description")

class SGAProductPackaging(models.Model):

    _inherit = "product.packaging"

    sga_uom_base_code = fields.Char(related='product_tmpl_id.uom_id.sga_uom_base_code')
    sga_desc_uom_base_code = fields.Char(related='product_tmpl_id.uom_id.name')
    sga_complete_percent = fields.Integer('SGA complete percent', default=100)
    sga_min_quantity = fields.Float('SGA min quantity', default=1)
    sga_operation = fields.Char('SGA Operation', default="A")
    sga_containertype_code_id = fields.Many2one('sga.containertype')
    sga_containertype_code = fields.Char(related="sga_containertype_code_id.name")
    sga_desc_containertype_code = fields.Char(related="sga_containertype_code_id.sga_desc_containertype_code")




    @api.model
    def default_get(self, fields):
        import ipdb;
        ipdb.set_trace()
        res = super(SGAProductPackaging, self).default_get(fields)
        if self._context.get('template_id') and 'model_id' in fields and not res.get('model_id'):
            res['model_id'] = self.env['mail.template'].browse(self._context['template_id']).model_id.id
        return res

    @api.model
    def create(self, vals):
        import ipdb;
        ipdb.set_trace()

        new_sga = super(SGAProductPackaging, self).create(vals)

        res = new_sga.product_tmpl_id.new_mecalux_file()
        new_sga.sga_operation = "M"
        return new_sga

    @api.multi
    def write(self, vals):
        import ipdb; ipdb.set_trace()
        if vals == {'sga_operation': 'M'}:
            res = self.product_tmpl_id.new_mecalux_file()
        return super(SGAProductPackaging, self).write(vals)

class SGAProductTemplate(models.Model):

    _inherit = "product.template"

    sga_change_material_abc= fields.Selection ([(0, "NO"),(1,"SI")], default=1)
    sga_material_abc_code = fields.Selection ([('A', 'A'), ('B', 'B'), ('C', 'C')], default="C")
    sga_product_type_code = fields.Char(related='categ_id.sga_producttype_code')
    sga_uom_base_code = fields.Char(related='uom_id.sga_uom_base_code')
    sga_desc_uom_base_code= fields.Char(related='uom_id.name')
    sga_stock = fields.Float('SGA Stock', help="Last PST from Mecalux")
    # sga_code = fields.Char("SGA Code File", default="PRO")
    sga_prod_shortdesc = fields.Char("SGA short description", size=50)
    sga_warehouse_code = fields.Char(related="warehouse_id.code")


    @api.multi
    def new_mecalux_file(self):
        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('product.template', ids, code='PRO')

        return True

    @api.multi
    def check_mecalux_stock(self):
        ids = [x.id for x in self]
        print ids
        new_sga_file = self.env['sga.file'].check_sga_file('product.template', ids, code='PST')

        return True

class SGAProductUOM(models.Model):
    _inherit = "product.uom"

    sga_uom_base_code = fields.Char("Sga uom base code", size=12, required=True)
    # sga_desc_uom_base_code = fields.Char("Sga description", size=30)


class ProductSupplier(models.Model):

    _inherit = "product.supplierinfo"

#
# class SGADeliveryCarrier(models.Model):
#
#     _inherit ="delivery.carrier"
#     sga_carrier_code = fields.Char("Carrier code", size=20, required=True, defatul="SGA CODE")
#
