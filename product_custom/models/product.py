# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api,  _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):

    _inherit = "product.template"

    volume = fields.Float(
        'Volume', compute='_compute_volume', inverse='_set_volume',
        help="The volume in m3.", store=True, digits=(10, 6))
    # Avoid translations in those fields because of slow performance when 
    # create a product.product with lang in context.
    name = fields.Char(translate=False)
    description = fields.Text(translate=False)
    description_sale = fields.Text(translate=False)
    description_picking = fields.Text(translate=False)
    description_purchase = fields.Text(translate=False)
    tag_names = fields.Char('Tags', compute='_compute_tag_names', store=True)
    web = fields.Boolean('Web', compute="_compute_web_state", store=True)

    @api.depends('tag_ids', 'tag_ids.web')
    def _compute_web_state(self):
        for template in self:
            template.web = any(x.web for x in template.tag_ids)

    @api.depends('tag_ids')
    def _compute_tag_names(self):
        for product in self:
            product.tag_names = ', '.join(x.name for x in product.tag_ids)


class ProductProduct(models.Model):

    _inherit = "product.product"

    volume = fields.Float('Volume', help="The volume in m3.", digits=(10, 6))
    force_web = fields.Selection([('yes', 'Visible'), ('no', 'No visible'),
                                  ('tags', 'Según etiquetas')], default='tags',
                                 string="Forzar web")

    attribute_names = fields.Char('Attributes', compute='_compute_attribute_names', store=True)
    web = fields.Boolean('Web', compute="_compute_web_state")
    tags_web = fields.Boolean(related="product_tmpl_id.web", string='Web (Plantilla)')


    # def apply_package_dimensions(self):
    #_sql_constraints = [
    #    ('uniq_default_code',
    #     'unique(default_code, archive)',
    #''     'The reference must be unique'),
    #'']

    @api.multi
    @api.constrains('default_code')
    def _check_company(self):
        if self.default_code:
            domain = [('default_code', '=', self.default_code), ('active','=', True)]
            if self.env['product.product'].search(domain):
                raise ValidationError(_('Rhe referencia must be unique'))

    @api.depends('force_web', 'tag_ids', 'product_tmpl_id.web')
    def _compute_web_state(self):
        for product in self:
            if product.force_web == 'yes':
                product.web = True
            elif product.force_web == 'no':
                product.web = False
            elif product.force_web == 'tags':
                product.web = product.product_tmpl_id.web

    @api.depends('attribute_value_ids')
    def _compute_attribute_names(self):
        for product in self:
            product.attribute_names = ', '.join(x.name_get()[0][1] for x in product.attribute_value_ids)


class ProductPackaging(models.Model):

    _inherit = "product.packaging"


    def compute_product_dimensions(self):
        if self.qty == 0:
            raise ValidationError(_("Check quantity !!!!"))
        self.product_tmpl_id.weight = self.max_weight / self.qty
        self.product_tmpl_id.volume = self.height * self.width * \
                self.length / (self.qty )

        for product in self.product_tmpl_id.product_variant_ids:
            product.weight = self.product_tmpl_id.weight
            product.volume = self.product_tmpl_id.volume

        return True


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    legacy_code = fields.Char("Legacy code", size=18)


class ProductTag(models.Model):
    _inherit = "product.tag"

    legacy_code = fields.Char("Legacy code", size=18)
