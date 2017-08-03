# -*- coding: utf-8 -*-
# © 2016 Comunitea Servicios Tecnologicos (<http://www.comunitea.com>)
# Kiko Sanchez (<kiko@comunitea.com>)
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html

from odoo import fields, models, tools, api, _

from odoo.exceptions import AccessError, UserError, ValidationError
from datetime import datetime, timedelta

import os
import re

SGA_STATE = [('AC', 'Actualizado'), ('PA', 'Pendiente actualizar'), ('BA', 'Baja'), ('ER', 'Error')]

class SGADestination(models.Model):

    _name ="sga.destination"

    code = fields.Char("Code")
    name = fields.Char("Description")

class SGAProductCategory(models.Model):

    _inherit = "product.category"
    code = fields.Char("Codigo de categoria", size=12)
    parent_code = fields.Char(related="parent_id.code")
    sga_state = fields.Selection(SGA_STATE,
                                 'Estado Mecalux',
                                 default='PA',
                                 help="Estado integracion con mecalux")

    _sql_constraints = [
        ('code_uniq', 'unique(code)', 'producttype code must be unique.'),
    ]

    @api.onchange('name', 'parent_id', 'code')
    def onchange_picking_type(self):
        for categ in self:
            categ.sga_state = 'PA'

    @api.multi
    def write(self, values):
        to_mecalux = False
        fields_to_check = ('name', 'parent_id', 'code')
        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            values['sga_state'] = 'PA'
            to_mecalux = True
        res = super(SGAProductCategory, self).write(values)

        if to_mecalux:
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
            res.sga_state = 'AC'
        return res

    def new_mecalux_file(self, operation='F'):
        return self.export_category_to_mecalux(self, operation=operation)

    @api.multi
    def export_category_to_mecalux(self, operation=False):

        def get_ids(cat):

            res = []
            while cat:
                if cat.sga_state != 'AC':
                    if not res:
                        res.append(cat.id)
                    elif not cat.sga_state:
                        res.append(cat.id)
                cat = cat.parent_id
            return res

        ids = [self.id]
        ctx = self._context.copy()
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
            self.env['product.category'].browse(ids).write({'sga_state': 'AC'})
            return True
        except:
            self.env['product.category'].browse(ids).write({'sga_state': 'ER'})
            return False

class SGAContainerTypeCode(models.Model):

    _name ="sga.containertype"
    _rec_name = 'code'

    code = fields.Char("Codigo de contenedor (SGA)", size=10)
    description = fields.Char("Descripcion de contenedor (SGA)")

class SGAProductPackaging(models.Model):

    _inherit = "product.packaging"

    ul_type = fields.Selection(selection_add=[('sga', 'Mecalux')])

    sga_uom_base_code = fields.Char(related='product_tmpl_id.uom_id.sga_uom_base_code')
    sga_desc_uom_base_code = fields.Char(related='product_tmpl_id.uom_id.name')
    sga_complete_percent = fields.Integer('SGA complete percent', default=1,
                                          help="Porcentaje para servir el palet completo")
    sga_min_quantity = fields.Float('SGA min quantity', default=1, help="Cantidad minima a servir")
    sga_operation = fields.Char('SGA Operation', default="A")
    sga_containertype_code_id = fields.Many2one('sga.containertype',
                                                "Tipo de contenedor",
                                                help="Tipo de contenedor de Mecalux")
    sga_containertype_code = fields.Char(related="sga_containertype_code_id.code")
    sga_desc_containertype_code = fields.Char(related="sga_containertype_code_id.description")

    @api.model
    def default_get(self, fields):
        res = super(SGAProductPackaging, self).default_get(fields)
        #### Que carallo hice aquí ?????
        if self._context.get('template_id') and 'model_id' in fields and not res.get('model_id'):
            res['model_id'] = self.env['mail.template'].browse(self._context['template_id']).model_id.id
        return res

    @api.model
    def create(self, vals):
        new_sga = super(SGAProductPackaging, self).create(vals)
        # si está asociado a un template
        if new_sga.product_tmpl_id:
            new_sga.product_tmpl_id.sga_state = 'PA'
            new_sga.product_tmpl_id.export_template_to_mecalux()
        return new_sga

    @api.multi
    def write(self, vals):
        res_write = super(SGAProductPackaging, self).write(vals)
        # Si están asociados a templates ....
        for pack in self:
            if pack.product_tmpl_id:
                pack.product_tmpl_id.sga_state = 'PA'
                pack.product_tmpl_id.export_template_to_mecalux()
        return res_write

class SGAProductProduct(models.Model):

    _inherit = "product.product"

    @api.multi
    def get_variant_name(self):
        for prod in self:
            sga_name_get = prod.name_get()[0][1]
            if ']' in sga_name_get:
                sga_name_get = sga_name_get.split(']')[1].strip()
            prod.sga_name_get = sga_name_get


    sga_name_get = fields.Char("Mecalux name", compute='get_variant_name')
    sga_prod_shortdesc = fields.Char("Nombre Radiofrecuencia", size=50)
    sga_stock = fields.Float('Stock (SGA)', help="Last PST from Mecalux")
    sga_change_material_abc = fields.Selection ([('0', "NO"), ('1', "SI")],
                                                default='1',
                                                string="Cambio rotabilidad",
                                                required=True)
    sga_material_abc_code = fields.Selection ([('A', 'A'), ('B', 'B'), ('C', 'C')],
                                              default="C",
                                              string="Tipo de rotabilidad",
                                              required=True)
    sga_state = fields.Selection(SGA_STATE,  'Estado Mecalux',
                                 default='PA',
                                 help="Estado integracion con mecalux")

    sga_product_type_code = fields.Char(related='categ_id.code')
    sga_uom_base_code = fields.Char(related='uom_id.sga_uom_base_code')
    sga_desc_uom_base_code = fields.Char(related='uom_id.name')
    sga_warehouse_code = fields.Char(related="warehouse_id.code")


    @api.onchange('name')
    def on_change(self):
        if self.name:
            self.sga_prod_shortdesc = self.sga_name_get[0:50]

    @api.multi
    def toggle_active(self):
        return super(SGAProductProduct, self).toggle_active()

    @api.multi
    def write(self, values):

        print "write de product con values %s"%values

        if not self.sga_prod_shortdesc and not values.get('sga_prod_shortdesc', False):
            values['sga_prod_shortdesc'] = self.sga_name_get[0:80]

        fields_to_check = ('default_code', 'barcode', 'categ_id',
                           'sga_material_abc_code', 'sga_change_material_abc',
                           'name', 'packaging_ids', 'sga_prod_shortdesc')

        fields = sorted(list(set(values).intersection(set(fields_to_check))))
        if fields:
            values['sga_state'] = 'PA'

        res = super(SGAProductProduct, self).write(values)

        #si viene de un create directo no hay write de fields distinto
        if self._context.get('create_product_product', False):
            create_product_product = True

        for product in self.filtered(lambda x: x.type == 'product'):
            create = False
            if product.sga_state != 'AC':
                for field in fields:
                    if product[field]:
                        create = True
                    continue

                if create or create_product_product:
                    new_mecalux_file = product.new_mecalux_file("F")
                    product.sga_state = "AC"

        return res

    @api.multi
    def export_product_to_mecalux(self, operation="F"):
        res = False
        for product in self:
            if product.type == "product":
                res = product.new_mecalux_file(operation)
        return res

    @api.model
    def create(self, values):
        return super(SGAProductProduct, self).create(values)


    @api.multi
    def new_mecalux_file(self, operation=False):
        try:
            ids = [x.id for x in self]
            ctx = self._context.copy()
            if operation:
                ctx['operation'] = operation
            if 'operation' not in ctx:
                ctx['operation'] = 'F'

            new_sga_file = self.env['sga.file'].with_context(ctx).check_sga_file('product.product', ids, code='PRO')
            return new_sga_file
        except:
            self.sga_state = 'ER'
            #self.write({'sga_state': 'NE'})
            return False

    @api.multi
    def check_mecalux_stock(self):
        try:
            ids = [x.id for x in self if x.type == 'product']
            if not ids:
                return
            new_sga_file = self.env['sga.file'].check_sga_file('product.product', ids, code='PST')
            return new_sga_file
        except:
            raise ValidationError("Error el generar el fichero de stock")

class SGAProductTemplate(models.Model):

    _inherit = "product.template"

    @api.model
    def _get_default_dst(self):
        domain = [('code', '=', 'TRASLO')]
        dst = self.env['sga.destination'].search(domain, limit=1)
        if dst:
            return dst

    sga_state = fields.Selection(SGA_STATE, 'Estado Mecalux',
                                 default='PA',
                                 help="Estado integracion con mecalux",
                                 compute='_compute_sga_state', readonly=True, store=False)
    sga_dst = fields.Many2one('sga.destination', 'Ubicación-Destino', default=_get_default_dst)
    sga_dst_code = fields.Char(related="sga_dst.code")

    @api.one
    def _compute_sga_state(self):
        sga_state = 'AC'
        for product in self.product_variant_ids:
            if product.sga_state != 'AC':
                sga_state = 'PA'
            if product.sga_state == 'ER':
                sga_state = 'ER'
                break
        self.sga_state = sga_state

    @api.one
    def _set_sga_state(self):
        for product in self.product_variant_ids:
            product.sga_state = self.sga_state

    @api.multi
    def export_template_to_mecalux(self):
        return self.new_mecalux_file()

    @api.multi
    def new_mecalux_file(self, operation=False):
        for template in self:
            if template.type == "product":
                for product in template.product_variant_ids:
                    product.export_product_to_mecalux(operation)
        return True

    @api.model
    def create(self, vals):
        #Necesito un packaging para para cada template, si no se crea al vuelo.
        if vals.get('type', False) == "product":
            create_sga_packaging = True
            if not vals.get('packaging_ids', False):
                vals['packaging_ids'] = []
            for sga_packaging in vals['packaging_ids']:
                if sga_packaging[2]['ul_type'] == 'sga':
                    create_sga_packaging = False
                    break
            if create_sga_packaging:
                sga_pack_vals = {
                    'ul_type': 'sga',
                    'qty': 500,
                    'name': 'Mecalux',
                    'sga_containertype_code_id':
                        self.env['sga.containertype'].search([('code', '=', 'EU')]).id
                    }
                vals['packaging_ids'].append([0, 0, sga_pack_vals])

        return super(SGAProductTemplate, self).create(vals)


    @api.multi
    def write(self, values):
        return super(SGAProductTemplate, self).write(values)


class SGAProductUOM(models.Model):
    _inherit = "product.uom"
    sga_uom_base_code = fields.Char("Codigo de u.m.(SGA)", size=12)
