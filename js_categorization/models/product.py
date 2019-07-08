# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ProductTemplate(models.Model):
    _inherit = "product.template"

    categorization_percent_filled = fields.Integer(string='Categorization Percent Completed', default=0, store=True)

    @api.model
    def calculate_categorization_percent(self):
        for record in self:
            categorization_percent = 0 # Record categorization percent
            custom_fields = 0.0 # Categorization fields counter
            filled_fields = 0.0 # Categorization filled fields counter
            # Get all categorization fields
            categorization_fields = self.env['js_categorization.field'].sudo().search([])
            # Get product categorization
            product_categorization = self.env['product.template.categorization'].search([('product_id', '=', record.id)])
            # Get variants categorization
            variants_categorization = self.env['product.product.categorization'].search([('product_id', 'in', record.product_variant_ids._ids)])
            # Loop categorization fields
            for field in categorization_fields:
                # If field not have type, and categorization_type is distinct of product template categorization type
                if not field.categorization_type or field.categorization_type == product_categorization.categorization_template:
                    # If field is for product
                    if field.model_id.model == 'product.template.categorization':
                        custom_fields += 1 # Add field to the counter
                        # If field exists and have value
                        if hasattr(product_categorization, field.name) and product_categorization[field.name]:
                            filled_fields += 1 # Add field to the counter
                    # If field is for variant
                    if field.model_id.model == 'product.product.categorization':
                        custom_fields += len(record.product_variant_ids) # Add field for each variant
                        if variants_categorization:
                            # Loop product variants
                            for variant_categorization in variants_categorization:
                                # If field exists and have value
                                if hasattr(variant_categorization, field.name) and variant_categorization[field.name]:
                                    filled_fields += 1 # Add field to the counter
            if custom_fields:
                # Calculate and save percent
                categorization_percent = int((filled_fields/custom_fields) * 100)
            record.categorization_percent_filled = categorization_percent

    @api.multi
    def categorization_modal(self):
        self.ensure_one() # One record expected
        # Get product categorization
        product_categorization = self.env['product.template.categorization'].search([('product_id', '=', self.id)])
        if not product_categorization:
            # Create product categorization
            product_categorization = self.env['product.template.categorization'].create({'product_id': self.id})

        return { # Open categorization popup
            'name': 'Product Categorization',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': product_categorization.id,
            'res_model': 'product.template.categorization',
            'type': 'ir.actions.act_window',
            'context': { 'default_product_id': self.id  },
            'target': 'new'
        }

    @api.multi
    def write(self, values):
        res = super(ProductTemplate, self).write(values)
        self.calculate_categorization_percent()
        return res

class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def categorization_modal(self):
        self.ensure_one() # One record expected
        # Get variant categorization
        variant_categorization = self.env['product.product.categorization'].search([('product_id', '=', self.id)])
        if not variant_categorization:
            # Create variant categorization
            variant_categorization = self.env['product.product.categorization'].create({'product_id': self.id})

        return { # Open categorization popup
            'name': 'Product Categorization',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': variant_categorization.id,
            'res_model': 'product.product.categorization',
            'type': 'ir.actions.act_window',
            'context': { 'default_product_id': self.id },
            'target': 'new'
        }

    @api.multi
    def write(self, values):
        res = super(ProductProduct, self).write(values)
        self.product_tmpl_id.calculate_categorization_percent()
        return res

class ProductCategorization(models.Model):
    _name = 'product.template.categorization'
    _description = "Product Categorization"
    _sql_constraints = [('categorization_product_unique', 'unique(product_id)', 'Product must be unique in categorization!')]
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.template', string='Related Product', required=True, ondelete='cascade')
    categorization_template = fields.Many2one('js_categorization.type', string='Template', required=False)

    @api.multi
    def new_field_modal(self):
        self.ensure_one() # One record expected
    	return { # Open new categorization field popup
            'name': 'Product Categorization Field',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'js_categorization.field',
            'type': 'ir.actions.act_window',
            'context': { 'default_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id },
            'target': 'new'
        }

    @api.multi
    def edit_variant(self):
        return { # Open variant selection wizard
            'name': 'Switch to Variant',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'gotoproduct.wizard',
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    @api.multi
    def go_to_product(self):
        self.ensure_one() # One record expected
    	return { # Go to product form
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.product_id.id,
            'res_model': 'product.template',
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def write(self, values):
        # If categorization template changed, empty not applicable fields
        # We did this instead of delete asociated categorization to avoid fill generic fields again
        if self.categorization_template != values.get('categorization_template'):
            categorization_fields = self.env['js_categorization.field'].sudo().search([])
            product_categorization = self.env['product.template.categorization'].search([('product_id', '=', self.product_id.id)])
            variants_categorization = self.env['product.product.categorization'].search([('product_id', 'in', self.product_id.product_variant_ids._ids)])
            for field in categorization_fields:
                if field.categorization_type and values.get('categorization_template', self.categorization_template) not in field.categorization_type:
                    if product_categorization:
                        super(ProductCategorization, product_categorization).write({ field.name: False })
                    if variants_categorization:
                        super(VariantCategorization, variants_categorization).write({ field.name: False })
        # Save and go to variant
        super(ProductCategorization, self).write(values)
        self.product_id.calculate_categorization_percent()
        return self.with_context(default_product_id=self.product_id.id).edit_variant()

    @api.multi
    def unlink(self):
        for record in self:
            # Copy product
            product = record.product_id
            # Delete variants categorization
            self.env['product.product.categorization'].search([('product_id', 'in', product.product_variant_ids._ids)]).unlink()
            # Delete product categorization
            super(ProductCategorization, record).unlink()
            # Set product categorization percent to 0
            product.categorization_percent_filled = 0

class VariantCategorization(models.Model):
    _name = 'product.product.categorization'
    _description = "Variant Categorization"
    _sql_constraints = [('categorization_variant_unique', 'unique(product_id)', 'Variant must be unique in categorization!')]
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Related Variant', required=True, ondelete='cascade')
    categorization_template = fields.Many2one('js_categorization.type', string='Template', compute='_get_product_template', store=False)

    @api.multi
    @api.depends('product_id')
    def _get_product_template(self):
        for record in self:
            if record.product_id:
                # Get parent template categorization
                product_template_categorization = self.env['product.template.categorization'].search([('product_id', '=', record.product_id.product_tmpl_id.id)])
                # Set parent template as variant template
                record.categorization_template = product_template_categorization.categorization_template

    @api.multi
    def new_field_modal(self):
        self.ensure_one() # One record expected
    	return { # Open new categorization field popup
            'name': 'Variant Categorization Field',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'js_categorization.field',
            'type': 'ir.actions.act_window',
            'context': { 'default_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id },
            'target': 'new'
        }

    @api.multi
    def edit_template(self):
        self.ensure_one() # One record expected
        return self.env['product.template'].browse(self.product_id.product_tmpl_id.id).categorization_modal()

    @api.multi
    def go_to_variant(self):
        self.ensure_one() # One record expected
    	return { # Go to variant form
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.product_id.id,
            'res_model': 'product.product',
            'type': 'ir.actions.act_window'
        }

    @api.multi
    def write(self, values):
        # Save and go to variant
        if super(VariantCategorization, self).write(values):
            self.product_id.product_tmpl_id.calculate_categorization_percent()
            return self.env['product.template.categorization'].with_context(default_product_id=self.product_id.product_tmpl_id.id).edit_variant()

    @api.multi
    def unlink(self):
        for record in self:
            # Copy parent product
            product = record.product_id.product_tmpl_id
            # Delete variant categorization
            super(VariantCategorization, record).unlink()
            # Re-calculate product categorization percent
            product.calculate_categorization_percent()
