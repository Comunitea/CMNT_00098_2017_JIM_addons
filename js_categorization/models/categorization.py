# -*- coding: utf-8 -*-
from odoo import models, fields

class CategorizationType(models.Model):
    _name = 'js_categorization.type'
    _description = "Categorization types"

    _sql_constraints = [
        ('categorization_type_unique', 'unique(name)', 'Type must be unique in categorization!'),
    ]

    name = fields.Char(required=True, translate=False)
    generic = fields.Boolean()

class CategorizationParam(models.Model):
    _name = 'js_categorization.param'
    _description = "Categorization parameters"
    _order = 'sequence, id'

    _sql_constraints = [
        ('categorization_param_unique', 'unique(type_id, name)', 'Parameter must be unique per Type!'),
    ]

    sequence = fields.Integer(default=10)
    name = fields.Char(required=True, translate=True)
    type_id = fields.Many2one('js_categorization.type', ondelete='cascade')
    value_ids = fields.Many2many('js_categorization.value', relation='categorization_param_value_rel')

class CategorizationValue(models.Model):
    _name = 'js_categorization.value'
    _description = "Categorization values"

    name = fields.Char(required=True, translate=True)
