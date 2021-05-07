# -*- coding: utf-8 -*-
from odoo import api, fields, models
from .. import constants

class ProductTemplate(models.Model):
    _inherit = "product.template"

    parameterization_percent_filled = fields.Integer(string='Parameterization Percent Completed', default=0, store=True, copy=False)

    @api.multi
    def get_parameterization(self):
        self.ensure_one()  # One record expected
        return self.env[constants.PRODUCT_PARAMETERIZATION].search([
            ('product_tmpl_id', '=', self.id)
        ], limit=1)

    @api.multi
    def create_parameterization(self, values=dict()):
        self.ensure_one()  # One record expected
        values.update({ 'product_tmpl_id': self.id })
        return self.env[constants.PRODUCT_PARAMETERIZATION].create(values)

    #public
    @api.multi
    def compute_parameterization_percent(self):
        for record in self:
            parameterization_percent = 0  # Record parameterization percent
            custom_fields = 0.0  # Parameterization fields counter
            filled_fields = 0.0  # Parameterization filled fields counter

            # Get product parameterization
            product_parameterization = record.get_parameterization()
            # Template applicable fields
            template_fields = product_parameterization.template_fields_get()
            # Get all parameterization fields
            parameterization_fields = self.env[constants.PRODUCT_PARAMETERIZATION].fields_get(template_fields)
            # Loop parameterization fields
            for field, attrs in parameterization_fields.items():
                custom_fields += 1 # Add field to the counter
                # If field exists and have value
                if hasattr(product_parameterization, field) and product_parameterization[field]:
                    filled_fields += 1 # Add field to the counter

            if custom_fields:
                # Calculate and save percent
                parameterization_percent = int((filled_fields/custom_fields) * 100)
            record.parameterization_percent_filled = parameterization_percent

    #public
    @api.multi
    def parameterization_modal(self):
        self.ensure_one()  # One record expected
        
        # Get product parameterization or create
        parameterization = self.get_parameterization() or self.create_parameterization()

        return {  # Open parameterization popup
            'name': 'Product Parameterization',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': parameterization.id,
            'res_model': constants.PRODUCT_PARAMETERIZATION,
            'type': 'ir.actions.act_window',
            'context': { 'default_product_tmpl_id': self.id },
            'target': 'current'
        }