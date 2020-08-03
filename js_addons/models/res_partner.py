# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class ResPartner(models.Model):
    _inherit = 'res.partner'

    group_companies_ids = fields.Many2many('res.company', string='Web Access')

    @api.model
    def create(self, vals):
        # Copiar campo group_companies_ids a vip_web_access
        # el campo group_companies_ids es usado por "prestadoo" mientras que
        # vip_web_access es usado por "js_b2b" (mientras se mantenga el módulo Prestadoo)
        if vals.get('group_companies_ids') and 'vip_web_access' in self:
            vals.update({ 'vip_web_access': vals['group_companies_ids'] })
        return super(ResPartner, self).create(vals)

    @api.multi
    def write(self, vals):
        # Copiar campo group_companies_ids a vip_web_access
        # el campo group_companies_ids es usado por "prestadoo" mientras que
        # vip_web_access es usado por "js_b2b" (mientras se mantenga el módulo Prestadoo)
        if vals.get('group_companies_ids') and 'vip_web_access' in self:
            vals.update({ 'vip_web_access': vals['group_companies_ids'] })
        return super(ResPartner, self).write(vals)