# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

class SGAProductCategory(models.Model):

    _inherit = "product.category"
    code = fields.Char("Codigo de categoria", size=12)
    parent_code = fields.Char(related="parent_id.code")
    sga_state = fields.Selection([(1, 'Actualizado'), (0, 'Pendiente actualizar')],
                                 default=0,
                                 help="Estado integracion con mecalux")

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'producttype code must be unique.'),
    ]

    @api.onchange('name', 'parent_id', 'code')
    def onchange_picking_type(self):
        for categ in self:
            categ.sga_state = 0

    @api.multi
    def write(self, values):
        res = super(SGAProductCategory, self).write(values)
        fields_to_check = ('name', 'parent_id', 'code')
        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            icp = self.env['ir.config_parameter']
            if icp.get_param('product_auto'):
                self.export_category_to_mecalux(operation="F")
        return res

    @api.model
    def create(self, values):
        icp = self.env['ir.config_parameter']
        res = super(SGAProductCategory, self).create(values)
        if icp.get_param('product_auto'):
            #Siempre F (modificacion + alta)
            res.export_category_to_mecalux(operation="F")
            res.sga_state = 1
        return res

    def new_mecalux_file(self, operation='F'):
        return self.export_category_to_mecalux(self, operation=operation)

    @api.multi
    def export_category_to_mecalux(self, operation=False):

        def get_ids(cat):

            res = []
            while cat:
                if cat.sga_state != 1:
                    if not res:
                        res.append(cat.id)
                    elif not cat.sga_state:
                        res.append(cat.id)
                cat = cat.parent_id
            return res
        ids = []
        ctx = dict(self.env.context)
        force = ctx.get('force', True)
        for x in self:
            ids += get_ids(x)

        ids = sorted(list(set(ids)))
        if not ids:
            raise ValidationError("No hay registros modificados para actualizar")

        if operation:
            ctx['operation'] = operation
        if 'operation' not in ctx:
            ctx['operation'] = 'F'
        try:
            new_sga_file = self.env['sga.file'].with_context(ctx).check_sga_file('product.category', ids, code='TPR')
            self.env['product.category'].browse(ids).write({'sga_state': 1})
            return True
        except:
            self.env['product.category'].browse(ids).write({'sga_state': 0})
            return False


class SGAContainerTypeCode(models.Model):

    _name ="sga.containertype"

    name = fields.Char("Codigo de contenedor (SGA)", size=10)
    sga_desc_containertype_code = fields.Char("Descripcion de contenedor (SGA)")

class SGAProductPackaging(models.Model):

    _inherit = "product.packaging"

    sga_uom_base_code = fields.Char(related='product_tmpl_id.uom_id.sga_uom_base_code')
    sga_desc_uom_base_code = fields.Char(related='product_tmpl_id.uom_id.name')
    sga_complete_percent = fields.Integer('SGA complete percent', default=100,
                                          help="Porcentaje para servir el palet completo")
    sga_min_quantity = fields.Float('SGA min quantity', default=1, help="Cantidad minima a servir")
    sga_operation = fields.Char('SGA Operation', default="A")
    sga_containertype_code_id = fields.Many2one('sga.containertype',
                                                "Tipo de contenedor",
                                                help="Tipo de contenedor")
    sga_containertype_code = fields.Char(related="sga_containertype_code_id.name")
    sga_desc_containertype_code = fields.Char(related="sga_containertype_code_id.sga_desc_containertype_code")

    @api.model
    def default_get(self, fields):

        res = super(SGAProductPackaging, self).default_get(fields)
        if self._context.get('template_id') and 'model_id' in fields and not res.get('model_id'):
            res['model_id'] = self.env['mail.template'].browse(self._context['template_id']).model_id.id
        return res

    @api.model
    def create(self, vals):

        new_sga = super(SGAProductPackaging, self).create(vals)
        new_sga.product_tmpl_id.sga_state = 0
        new_sga.sga_operation = "A"
        return new_sga

    @api.multi
    def write(self, vals):
        for pack in self:
            pack.product_tmpl_id.sga_state_id = 0
        res_write = super(SGAProductPackaging, self).write(vals)
        return res_write

class SGAProductProduct(models.Model):

    _inherit = "product.product"

    sga_prod_shortdesc = fields.Char("Nombre Radiofrecuencia", size=50, required=1)
    sga_stock = fields.Float('Stock (SGA)', help="Last PST from Mecalux")
    sga_state = fields.Selection([(1, 'Actualizado'), (0, 'Pendiente actualizar'), (2, 'Baja')],
                                 default=False,
                                 help="Estado integracion con mecalux")

    @api.onchange('name')
    def on_change(self):
        if not self.sga_prod_shortdesc and self.name:
            self.sga_prod_shortdesc = self.name[0:50]

    @api.multi
    def toggle_active(self):
        res = super(SGAProductProduct, self).toggle_active()
        for record in self:
            if record.active:
                operation = "F"
            else:
                operation = "B"
            print "toggle active desde product"
            record.new_mecalux_file(operation=operation)
            record.sga_state = 1

    @api.multi
    def write(self, values):
        res = super(SGAProductProduct, self).write(values)
        if self.type != 'product':
            return res
        fields_to_check = ('default_code', 'barcode', 'categ_id', 'sga_state'
                           'sga_material_abc_code', 'sga_change_material_abc',
                           'uom_id', 'name', 'sga_prod_shortdesc', 'packaging_ids')
        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            icp = self.env['ir.config_parameter']
            if icp.get_param('product_auto'):
                self.new_mecalux_file(operation="F")
        return res

    @api.multi
    def export_product_to_mecalux(self):
        for product in self:

            if product.type == "product":
                if product.packaging_ids:
                    res = product.new_mecalux_file(operation="F")
                else:
                    raise ValidationError("Necesitas definir un empaquetado para %s"%product.name)
        return res


    @api.model
    def create(self, values):

        res = super(SGAProductProduct, self).create(values)
        if self.type != 'product':
            return res
        icp = self.env['ir.config_parameter']
        if icp.get_param('product_auto'):
            self.new_mecalux_file(operation="F")
        return res

    @api.multi
    def new_mecalux_file(self, operation=False):
        try:
            ids = [x.id for x in self]
            ctx = dict(self.env.context)
            if operation:
                ctx['operation'] = operation
            if 'operation' not in ctx:
                ctx['operation'] = 'F'
            new_sga_file = self.env['sga.file'].with_context(ctx).check_sga_file('product.product', ids, code='PRO')
            self.write({'sga_state': 1})
            return True
        except:
            self.write({'sga_state': 0})
            return True

    @api.multi
    def check_mecalux_stock(self):
        try:
            ids = [x.id for x in self if self.type == 'product']
            if not ids:
                return
            new_sga_file = self.env['sga.file'].check_sga_file('product.product', ids, code='PST')
            return True
        except:
            raise ValidationError("Error el generar el fichero de stock")

class SGAProductTemplate(models.Model):

    _inherit = "product.template"

    @api.model
    def _get_default_dst(self):

        domain = [('code', '=', 'TRASLO')]
        dst = self.env['product.category'].search(domain, limit=1)
        if dst:
            return dst

    sga_prod_shortdesc = fields.Char("Nombre Radiofrecuencia", size=50,)
    sga_change_material_abc = fields.Selection ([('0', "NO"),('1',"SI")], default='1', string ="Cambio rotabilidad")
    sga_material_abc_code = fields.Selection ([('A', 'A'), ('B', 'B'), ('C', 'C')], default="C", string="Tipo de rotabilidad")
    sga_product_type_code = fields.Char(related='categ_id.code')
    sga_uom_base_code = fields.Char(related='uom_id.sga_uom_base_code')
    sga_desc_uom_base_code= fields.Char(related='uom_id.name')
    sga_warehouse_code = fields.Char(related="warehouse_id.code")
    sga_dst = fields.Many2one('product.category', 'Destino', default=_get_default_dst)
    sga_dst_code = fields.Char(related="sga_dst.code")
    type = fields.Selection(default='product')
    packaging_ids = fields.One2many(required=1)

    @api.onchange('name')
    def on_change(self):
        if not self.sga_prod_shortdesc and self.name:
            self.sga_prod_shortdesc = self.name[0:50]

    @api.multi
    def export_product_to_mecalux(self):
        return self.new_mecalux_file()

    @api.multi
    def new_mecalux_file(self, operation=False):
        for template in self:
            if template.type == "product":
                for product in template.product_variant_ids:
                    product.new_mecalux_file(operation)
        return True

    @api.model
    def create(self, vals):
        return super(SGAProductTemplate, self).create(vals)


    @api.multi
    def write(self, values):
        return super(SGAProductTemplate, self).write(values)

        if self.type != 'product':
            return res

        fields_to_check = ('default_code', 'barcode', 'categ_id', 'sga_state', 'sga_material_abc_code', 'sga_change_material_abc',
                           'uom_id', 'name', 'sga_prod_shortdesc', 'packaging_ids')
        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            icp = self.env['ir.config_parameter']
            if icp.get_param('product_auto'):
                self.new_mecalux_file(operation="F")
        return res

class SGAProductUOM(models.Model):
    _inherit = "product.uom"

    sga_uom_base_code = fields.Char("Codigo de u.m.(SGA)", size=12, required=True)

class ProductSupplier(models.Model):

    _inherit = "product.supplierinfo"

#
# class SGADeliveryCarrier(models.Model):
#
#     _inherit ="delivery.carrier"
#     sga_carrier_code = fields.Char("Carrier code", size=20, required=True, default="SGA CODE")
#
