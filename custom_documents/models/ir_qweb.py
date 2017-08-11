# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api, exceptions, _
from odoo.tools import html_escape as escape


class Contact(models.AbstractModel):
    _inherit = 'ir.qweb.field.contact'

    @api.model
    def value_to_html(self, value, options):
        res = super(Contact,self).value_to_html(value, options)
        if options.get('min_name', False):
            if not value.exists():
                return False

            opf = options and options.get('fields') or ["name", "address", "phone", "mobile", "fax", "email"]
            value = value.sudo().with_context(show_address=True)
            name_get = value.name or ''
            val = {
                'name': name_get.split("\n")[0],
                'address': escape("\n".join(value.name_get()[0][1].split("\n")[1:])).strip(),
                'phone': value.phone,
                'mobile': value.mobile,
                'fax': value.fax,
                'city': value.city,
                'country_id': value.country_id.display_name,
                'website': value.website,
                'email': value.email,
                'fields': opf,
                'object': value,
                'options': options
            }
            return self.env['ir.qweb'].render('base.contact', val)
        else:
            return res
