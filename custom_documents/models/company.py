# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields, api


class ResCompany(models.Model):

    _inherit = 'res.company'

    qweb_footer = fields.Html(translate=True)
    qweb_invoice_footer = fields.Html(translate=True)
    show_discount = fields.Boolean(default=True)
    iso_logo = fields.Binary()
    secure_logo = fields.Binary()
    hide_fields = fields.Boolean()
    iso_purchase_order_text = fields.Html(translate=True)
    company_advise = fields.Html(translate=True)
    show_company_advise = fields.Boolean("Mostrar texto al final del doc", default=False)
    class_page = fields.Char(compute="compute_class_page")

    @api.multi
    def compute_class_page(self):
        for company_id in self:
            company_id.class_page = company_id.show_company_advise and 'not-last-page' or ''
