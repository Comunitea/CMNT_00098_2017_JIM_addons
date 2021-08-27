# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):

    _inherit = "product.template"

    # Avoid translations in those fields because of slow performance when
    # create a product.product with lang in context.
    description = fields.Text(translate=False)
    description_sale = fields.Text(translate=False)
    description_picking = fields.Text(translate=False)
    description_purchase = fields.Text(translate=False)
    tag_names = fields.Char("Tags", compute="_compute_tag_names", store=True)
    list_price = fields.Float(default=0.0)

    @api.depends("public_categ_ids")
    def _compute_tag_names(self):
        for product in self:
            product.tag_names = ", ".join(x.name for x in
                                          product.public_categ_ids)


class ProductProduct(models.Model):

    _inherit = "product.product"

    attribute_names = fields.Char(
        "Attributes", compute="_compute_attribute_names", store=True
    )

    # def apply_package_dimensions(self):
    # _sql_constraints = [
    #    ('uniq_default_code',
    #     'unique(default_code, archive)',
    #''     'The reference must be unique'),
    #'']

    @api.constrains("default_code", "type")
    def _check_company(self):
        for product in self:
            if product.default_code:
                domain = [
                    ("default_code", "=ilike", product.default_code),
                    ("type", "=", "product"),
                    ("id", "!=", product.id),
                ]
                flds = ["display_name"]
                product_ids = self.env["product.product"].search_read(
                    domain, flds
                )
                if product_ids:
                    raise ValidationError(
                        _("Este código ya está asignado a otro artículo")
                    )
            if product.product_tmpl_id:
                domain = [
                    ("template_code", "=ilike", product.default_code),
                    ("type", "=", "product"),
                    ("id", "!=", product.product_tmpl_id.id),
                ]
                flds = ["display_name"]
                product_ids = self.env["product.template"].search_read(
                    domain, flds
                )
                if product_ids:
                    raise ValidationError(
                        _(
                            "Este código ya está asignado a otro artículo (plantilla)"
                        )
                    )

    @api.depends("product_template_attribute_value_ids")
    def _compute_attribute_names(self):
        for product in self:
            product.attribute_names = ", ".join(
                x.name_get()[0][1] for x in product.
                product_template_attribute_value_ids
            )


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    legacy_code = fields.Char("Legacy code", size=18)


class ProductCategory(models.Model):

    _inherit = "product.category"

    active = fields.Boolean(default=True)
    legacy_code = fields.Char("Legacy code", size=18)
    web = fields.Boolean("Web", default=True)
    image = fields.Binary('Image', attachment=True)
    child_id = fields.One2many(
        domain=["|", ("active", "=", True), ("active", "=", False)]
    )
    sequence = fields.Integer()
