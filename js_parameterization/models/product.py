# -*- coding: utf-8 -*-
from odoo import api, fields, models

class ProductTemplate(models.Model):
    _inherit = "product.template"

    parameterization_percent_filled = fields.Integer(string='Parameterization Percent Completed', default=0, store=True)

    #public
    @api.model
    def calculate_parameterization_percent(self):
        for record in self:
            parameterization_percent = 0  # Record parameterization percent
            custom_fields = 0.0  # Parameterization fields counter
            filled_fields = 0.0  # Parameterization filled fields counter
            # Get all parameterization fields
            parameterization_fields = self.env['js_parameterization.field'].sudo().search([])
            # Get product parameterization
            product_parameterization = self.env['product.template.parameterization'].search([('product_id', '=', record.id)])
            # Get variants parameterization
            variants_parameterization = self.env['product.product.parameterization'].search([('product_id', 'in', record.product_variant_ids._ids)])
            # Loop parameterization fields
            for field in parameterization_fields:
                # If field not have type, and parameterization_type is distinct of product template parameterization type
                if not field.parameterization_type or product_parameterization.parameterization_template.id == field.parameterization_type.id:
                    # If field is for product
                    if field.model_id.model == 'product.template.parameterization':
                        custom_fields += 1  # Add field to the counter
                        # If field exists and have value
                        if hasattr(product_parameterization, field.name) and product_parameterization[field.name]:
                            filled_fields += 1  # Add field to the counter
                    # If field is for variant
                    if field.model_id.model == 'product.product.parameterization':
                        custom_fields += len(record.product_variant_ids)  # Add field for each variant
                        if variants_parameterization:
                            # Loop product variants
                            for variant_parameterization in variants_parameterization:
                                # If field exists and have value
                                if hasattr(variant_parameterization, field.name) and variant_parameterization[field.name]:
                                    filled_fields += 1  # Add field to the counter
            if custom_fields:
                # Calculate and save percent
                parameterization_percent = int((filled_fields/custom_fields) * 100)
            record.parameterization_percent_filled = parameterization_percent

    #public
    @api.multi
    def parameterization_modal(self):
        self.ensure_one()  # One record expected
        
        # Get product parameterization
        product_parameterization = self.env['product.template.parameterization'].search([('product_id', '=', self.id)])
        if not product_parameterization:
            # Create product parameterization
            product_parameterization = self.env['product.template.parameterization'].create({'product_id': self.id})

        return {  # Open parameterization popup
            'name': 'Product Parameterization',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': product_parameterization.id,
            'res_model': 'product.template.parameterization',
            'type': 'ir.actions.act_window',
            'context': {'default_product_id': self.id},
            'target': 'new'
        }

class ProductProduct(models.Model):
    _inherit = "product.product"

    #public
    @api.multi
    def parameterization_modal(self):
        self.ensure_one()  # One record expected

        # Get variant parameterization
        variant_parameterization = self.env['product.product.parameterization'].search([('product_id', '=', self.id)])
        if not variant_parameterization:
            # Create variant parameterization
            variant_parameterization = self.env['product.product.parameterization'].create({'product_id': self.id})

        return {  # Open parameterization popup
            'name': 'Product Parameterization',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': variant_parameterization.id,
            'res_model': 'product.product.parameterization',
            'type': 'ir.actions.act_window',
            'context': {'default_product_id': self.id},
            'target': 'new'
        }

class ProductParameterization(models.Model):
    _name = 'product.template.parameterization'
    _description = "Product Parameterization"
    _sql_constraints = [('parameterization_product_unique', 'unique(product_id)', 'Product must be unique in parameterization!')]
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.template', string='Related Product', required=True, ondelete='cascade')
    parameterization_template = fields.Many2one('js_parameterization.type', string='Template', required=False)
    active = fields.Boolean('Active', default=True, related='product_id.active', store=False)

    #override
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(ProductParameterization, self).fields_get(allfields, attributes=attributes)
        for field in fields:
            field_obj = self.env['js_parameterization.field'].search([('name', '=', field)])
            if field_obj and field_obj.parameterization_type:
                fields[field]['string'] += ' [%s]' % field_obj.parameterization_type.name.upper()
        return fields

    #public
    @api.multi
    def new_field_modal(self):
        self.ensure_one()  # One record expected
        return {  # Open new parameterization field popup
            'name': 'Product Parameterization Field',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'js_parameterization.field',
            'type': 'ir.actions.act_window',
            'context': { 'default_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id },
            'target': 'new'
        }

    #public
    @api.multi
    def edit_variant(self):
        self.ensure_one()  # One record expected

        # If only have one variant go directly
        if (len(self.product_id.product_variant_ids) == 1):
            return self.product_id.product_variant_id.parameterization_modal()

        return { # Else open variant selection wizard
            'name': 'Switch to Variant',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'gotoproduct.wizard',
            'context': self.env.context,
            'type': 'ir.actions.act_window',
            'target': 'new'
        }

    #public
    @api.multi
    def go_to_product(self):
        self.ensure_one()  # One record expected
        return {  # Go to product form
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.product_id.id,
            'res_model': 'product.template',
            'type': 'ir.actions.act_window'
        }

    #override
    @api.multi
    def write(self, values):
        reset_fields = dict()

        # If parameterization template changed, empty not applicable fields
        # We did this instead of delete asociated parameterization to avoid fill generic fields again
        if values.get('parameterization_template') and self.parameterization_template.id != values['parameterization_template']:
            parameterization_fields = self.env['js_parameterization.field'].sudo().search([])
            for field in parameterization_fields:
                if field.parameterization_type and values.get('parameterization_template', self.parameterization_template.id) != field.parameterization_type.id:
                    reset_fields.update({ field.name: False })
                    
        # Reset fields
        if reset_fields:
            values.update(reset_fields)
            self.env['product.product.parameterization'].search([('product_id', 'in', self.product_id.product_variant_ids._ids)]).write(reset_fields)

        # Save & calculate percent
        super(ProductParameterization, self).write(values)
        self.product_id.calculate_parameterization_percent()

        # Variant wizard
        return self.with_context(default_product_id=self.product_id.id).edit_variant()

    #override
    @api.multi
    def unlink(self):
        for record in self:
            # Copy product
            product = record.product_id
            # Delete variants parameterization
            self.env['product.product.parameterization'].search([('product_id', 'in', product.product_variant_ids._ids)]).unlink()
            # Delete product parameterization
            super(ProductParameterization, record).unlink()
            # Set product parameterization percent to 0
            product.parameterization_percent_filled = 0

class VariantParameterization(models.Model):
    _name = 'product.product.parameterization'
    _description = "Variant Parameterization"
    _sql_constraints = [('parameterization_variant_unique', 'unique(product_id)', 'Variant must be unique in parameterization!')]
    _rec_name = 'product_id'

    product_id = fields.Many2one('product.product', string='Related Variant', required=True, ondelete='cascade')
    parameterization_template = fields.Many2one('js_parameterization.type', string='Template', compute='_get_product_template', store=False)
    active = fields.Boolean('Active', default=True, related='product_id.active', store=False)

    #override
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        fields = super(VariantParameterization, self).fields_get(allfields, attributes=attributes)
        for field in fields:
            field_obj = self.env['js_parameterization.field'].search([('name', '=', field)])
            if field_obj and field_obj.parameterization_type:
                fields[field]['string'] += ' [%s]' % field_obj.parameterization_type.name.upper()
        return fields

    #private
    @api.multi
    @api.depends('product_id')
    def _get_product_template(self):
        for record in self:
            if record.product_id:
                # Get parent template parameterization
                product_template_parameterization = self.env['product.template.parameterization'].search([('product_id', '=', record.product_id.product_tmpl_id.id)])
                # Set parent template as variant template
                record.parameterization_template = product_template_parameterization.parameterization_template

    #public
    @api.multi
    def new_field_modal(self):
        self.ensure_one() # One record expected
        return { # Open new parameterization field popup
            'name': 'Variant Parameterization Field',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'js_parameterization.field',
            'type': 'ir.actions.act_window',
            'context': { 'default_model_id': self.env['ir.model'].search([('model', '=', self._name)]).id },
            'target': 'new'
        }

    #public
    @api.multi
    def edit_template(self):
        self.ensure_one()  # One record expected
        return self.env['product.template'].browse(
            self.product_id.product_tmpl_id.id).parameterization_modal()

    #public
    @api.multi
    def go_to_variant(self):
        self.ensure_one()  # One record expected
        return {  # Go to variant form
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.product_id.id,
            'res_model': 'product.product',
            'type': 'ir.actions.act_window'
        }

    #override
    @api.multi
    def write(self, values):
        # Save and go to variant
        super(VariantParameterization, self).write(values)
        self.product_id.product_tmpl_id.calculate_parameterization_percent()
        return self.env['product.template.parameterization'].with_context(default_product_id=self.product_id.product_tmpl_id.id).edit_variant()

    #override
    @api.multi
    def unlink(self):
        for record in self:
            # Copy parent product
            product = record.product_id.product_tmpl_id
            # Delete variant parameterization
            super(VariantParameterization, record).unlink()
            # Re-calculate product parameterization percent
            product.calculate_parameterization_percent()