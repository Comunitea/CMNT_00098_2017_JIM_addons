# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import models, fields


class ResCompany(models.Model):

    _inherit = 'res.company'

    qweb_footer = fields.Html(translate=True)
    qweb_invoice_footer = fields.Html(translate=True)
    show_discount = fields.Boolean(default=True)
    iso_logo = fields.Binary()
    hide_fields = fields.Boolean()
    iso_purchase_order_text = fields.Html(translate=True)