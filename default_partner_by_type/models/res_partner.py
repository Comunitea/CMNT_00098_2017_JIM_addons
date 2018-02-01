# -*- coding: utf-8 -*-
# Copyright 2017 Omar Castiñeira, Comunitea Servicios Tecnológicos S.L.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class ResPartner(models.Model):

    _inherit = "res.partner"

    default_partner_by_type = fields.Boolean("Default partner by type")

    @api.multi
    @api.constrains("partner_id", "type", "default_partner_by_type")
    def _check_default_partner_by_type(self):
        """Ensure details are given if required."""
        for partner in self:
            domain = (('parent_id', '=', partner.parent_id.id), ('type', '=', partner.type), ('default_partner_by_type','=',True))
            if partner.search_count(domain) > 1:
                raise ValidationError (_('Only one default by partner type for each child'))


    @api.multi
    def address_get(self, adr_pref=None):
        for partner in self:
            partner.child_ids = partner.child_ids.sorted(key=lambda r: (r.type and -4 or 0) + (r.default_partner_by_type and -2 or 0) + (r.display_name and -1))
        return super(ResPartner, self).address_get(adr_pref)


    def set_as_default(self):
        if self.parent_id and not self.default_partner_by_type:
            domain = (('id','!=', self.id), ('parent_id', '=', self.parent_id.id), ('type', '=', self.type), ('default_partner_by_type', '=', True))
            not_defaults = self.search(domain)
            if not_defaults:
                not_defaults.write({'default_partner_by_type': False})
        self.default_partner_by_type = not self.default_partner_by_type
