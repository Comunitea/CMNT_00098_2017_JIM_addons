# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models
import odoo.addons.decimal_precision as dp


class CustomerPrice(models.Model):
    _name = "customer.price"

    product_tmpl_id = fields.Many2one('product.template', 'Template',
                                      index=1)
    product_id = fields.Many2one('product.product', 'Product', index=1)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True,
                                 index=1)
    min_qty = fields.Float('Min Quantity', default=0.0, required=True)
    price = fields.Float(
        'Price', default=0.0, digits=dp.get_precision('Product Price'),
        required=True, help="The price to purchase a product")
    date_start = fields.Date('Start Date', index=1,
                             help="Start date for this customer price")
    date_end = fields.Date('End Date', index=1,
                           help="End date for this customer price")
    company_id = fields.\
        Many2one('res.company', 'Company',
                 default=lambda self: self.env.user.company_id.id, index=1)
